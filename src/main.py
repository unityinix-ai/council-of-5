#!/usr/bin/env python3
"""Council of 5 — dispatch server.

Listens on --addr (default 0.0.0.0:50051, matching the Dockerfile) and fans
tasks out to the five council seats. A seat that fails never sinks the
council: its failure is reported in its own reply and the rest still speak.
"""

import argparse
import logging
from concurrent import futures

import grpc

import council_pb2
import council_pb2_grpc
from adapters import NotConfiguredError, build_council

log = logging.getLogger("council")


class CouncilServicer(council_pb2_grpc.CouncilServicer):
    def __init__(self, seats):
        self.seats = seats

    def Dispatch(self, request, context):
        replies = []
        wanted = set(request.seats)
        for seat in self.seats:
            if wanted and seat.name not in wanted:
                continue
            try:
                output = seat.complete(request.prompt)
                replies.append(
                    council_pb2.MemberReply(seat=seat.name, status="ok", output=output)
                )
            except NotConfiguredError as exc:
                replies.append(
                    council_pb2.MemberReply(
                        seat=seat.name, status="not_configured", error=str(exc)
                    )
                )
            except Exception as exc:  # noqa: BLE001 — one bad seat must not kill the council
                log.exception("seat %s failed", seat.name)
                replies.append(
                    council_pb2.MemberReply(seat=seat.name, status="error", error=str(exc))
                )
        return council_pb2.TaskResponse(task_id=request.task_id, replies=replies)


def main():
    parser = argparse.ArgumentParser(description="Council of 5 dispatch server")
    parser.add_argument("--addr", default="0.0.0.0:50051",
                        help="address to listen on (default 0.0.0.0:50051)")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )

    seats = build_council()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    council_pb2_grpc.add_CouncilServicer_to_server(CouncilServicer(seats), server)
    server.add_insecure_port(args.addr)
    server.start()
    log.info(
        "Council of 5 listening on %s — seats: %s",
        args.addr,
        [s.name for s in seats],
    )
    server.wait_for_termination()


if __name__ == "__main__":
    main()
