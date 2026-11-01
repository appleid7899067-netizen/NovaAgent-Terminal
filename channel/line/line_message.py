from channel.chat_message import ChatMessage


class LineMessage(ChatMessage):
    def __init__(self, event):
        msg_id = getattr(event, "webhook_event_id", "") or ""
        content = ""
        ctype = None
        try:
            if getattr(event, "message", None) is not None:
                content = getattr(event.message, "text", "") or ""
        except Exception:
            content = ""
        from bridge.context import ContextType
        ctype = ContextType.TEXT
        super().__init__(
            msg_id=msg_id,
            content=content,
            ctype=ctype,
            from_user_id=getattr(getattr(event, "source", None), "user_id", "") or "",
            to_user_id="",
            other_user_id="",
        )
        self.event = event
