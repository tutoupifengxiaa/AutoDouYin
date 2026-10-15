class BrowserController:
    def focus(self, title_keyword: str) -> bool:
        import pygetwindow as gw

        keyword = title_keyword.lower()
        for window in gw.getAllWindows():
            title = getattr(window, "title", "") or ""
            if keyword in title.lower():
                window.activate()
                return True
        return False
