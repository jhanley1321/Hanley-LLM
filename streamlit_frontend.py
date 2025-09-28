import os, json, requests
import streamlit as st
from dotenv import load_dotenv

class StreamlitChatApp:
    def __init__(self):
        load_dotenv()
        self.backend_url = os.getenv("BACKEND_URL", "http://127.0.0.1:8000/chat")
        self.prefill_token = os.getenv("HANLEY_LLM_SECRET_TOKEN", "")
        if "auth_token" not in st.session_state:
            st.session_state.auth_token = self.prefill_token
        if "connected" not in st.session_state:
            st.session_state.connected = False
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def headers(self):
        tok = st.session_state.auth_token or ""
        return {"Authorization": f"Bearer {tok}"} if tok else {}

    def test_connection(self):
        try:
            r = requests.post(self.backend_url, json={"message": "ping"}, headers=self.headers(), timeout=10)
            st.session_state.connected = r.ok
            return r.ok, r.status_code, (r.text or "OK")
        except Exception as e:
            st.session_state.connected = False
            return False, None, str(e)

    def stream_chat(self, prompt):
        try:
            r = requests.post(self.backend_url, json={"message": prompt}, headers=self.headers(), stream=True, timeout=120)
            r.raise_for_status()
        except Exception as e:
            yield {"error": str(e)}; return
        for raw in r.iter_lines(decode_unicode=True):
            if not raw: continue
            if not raw.startswith("data:"): continue
            data = raw[5:].strip()
            if data.upper() == "[DONE]": break
            if data.startswith("[ERROR]"):
                yield {"error": data}; break
            try:
                parsed = json.loads(data)
                delta = parsed.get("delta") if isinstance(parsed, dict) else parsed
            except json.JSONDecodeError:
                delta = data
            yield {"delta": delta}

    def sidebar(self):
        st.sidebar.title("Settings")
        page = st.sidebar.selectbox("Page", ["Chat", "API Connection"])
        with st.sidebar.expander("Authentication", expanded=True):
            token = st.text_input("Bearer token", value=st.session_state.auth_token, type="password")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Connect"):
                    st.session_state.auth_token = token
                    ok, code, msg = self.test_connection()
                    st.toast("Connected" if ok else f"Failed ({code})", icon="✅" if ok else "❌")
            with c2:
                if st.button("Disconnect"):
                    st.session_state.connected = False
                    st.session_state.auth_token = ""
        status = "Connected" if st.session_state.connected else "Not connected"
        st.sidebar.write(f"Status: {status}")
        return page

    def chat_page(self):
        st.title("OpenLLM Chat")
        if not st.session_state.connected:
            st.warning("Please authenticate and Connect from the sidebar.")
            return
        for m in st.session_state.messages:
            role = "You" if m["role"] == "user" else "Assistant"
            st.markdown(f"**{role}:** {m['content']}")
        prompt = st.text_input("Message", key="prompt")
        if st.button("Send") and prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            ph = st.empty(); full = ""; ph.markdown("**Assistant:** _streaming..._")
            for part in self.stream_chat(prompt):
                if "error" in part:
                    ph.error(part["error"]); full = f"Error: {part['error']}"; break
                full += part.get("delta") or ""
                ph.markdown(f"**Assistant:** {full}\u258c")
            ph.markdown(f"**Assistant:** {full}")
            st.session_state.messages.append({"role": "assistant", "content": full})

    def api_page(self):
        st.title("API Connection")
        st.write("Backend URL:", self.backend_url)
        if st.button("Check connection"):
            ok, code, msg = self.test_connection()
            if ok: st.success("Connected to backend")
            else: st.error(f"Failed ({code}): {msg}")

    def run(self):
        # Configure layout on run to avoid duplicate set_page_config
        try:
            st.set_page_config(page_title="OpenLLM Chat", layout="centered")
        except Exception:
            pass
        page = self.sidebar()
        if page == "Chat": self.chat_page()
        else: self.api_page()

if __name__ == "__main__":
    StreamlitChatApp().run()
