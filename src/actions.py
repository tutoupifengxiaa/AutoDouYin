class ActionExecutor:
    def run(self, mode: str, amount: int) -> None:
        import pyautogui

        if mode == "page_down":
            pyautogui.press("pagedown")
            return
        if mode == "page_up":
            pyautogui.press("pageup")
            return
        if mode == "scroll_down":
            pyautogui.scroll(amount)
            return
        if mode == "scroll_up":
            pyautogui.scroll(abs(amount))
            return
        raise ValueError(f"Unsupported scroll mode: {mode}")
