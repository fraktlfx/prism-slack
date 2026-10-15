import os
import sys


def setupPaths():
    sys.path.append(os.getenv("BOLTPATH", default=""))
    sys.path.append(os.getenv("SCRIPTSPATH", default=""))
    sys.path.append(os.getenv("PRISMPATH", default=""))
    sys.path.append(os.getenv("PRISM_CORE", default=""))
    sys.path.append(os.getenv("PRISM_UTILS", default=""))
    sys.path.append(os.getenv("PRISMPATH", default=""))
    sys.path.extend(os.getenv("PATH", default="").split(";"))


setupPaths()

import PrismCore
from prism_slack.server.blocks import SlackBlocks
from prism_slack.server.events import SlackEvents
from slack_bolt import App


class SlackBoltServer:
    def __init__(self, token: str, app_token: str):
        self.token = token
        self.app_token = app_token
        self.app = App(token=self.token)

        pcore = PrismCore.create(prismArgs=["noUI"])

        self.blocks = SlackBlocks()

        # Initialize the Slack Events to be used in the Slack Bolt Server
        self.events = SlackEvents(self.app, token, core=pcore)


if __name__ == "__main__":
    from slack_bolt.adapter.socket_mode import SocketModeHandler

    # Start the Slack Bolt Server
    bolt = SlackBoltServer(sys.argv[1], sys.argv[2])
    SocketModeHandler(bolt.app, bolt.app_token).start()
