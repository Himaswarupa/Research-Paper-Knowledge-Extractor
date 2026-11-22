import { useEffect, useRef, useState } from "react";
import { getPapers, getStatus, uploadPaper } from "../api";

const BUSY = ["uploading", "queued", "processing"];

export default function UploadPanel({ onDone }) {
  const [paper, setPaper] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const timer = useRef(null);

  const stopPolling = () => clearInterval(timer.current);

  const startPolling = (name) => {
    stopPolling();
    timer.current = setInterval(async () => {
      try {
        const s = await getStatus(name);
        setStatus(s.status);
        if (s.status === "done") {
          stopPolling();
          onDone();
        } else if (s.status.startsWith("failed")) {
          stopPolling();
          setError(s.status);
        }
      } catch (e) {
        stopPolling();
        setError(e.message);
      }
    }, 3000);
  };

  useEffect(() => {
    getPapers()
      .then((list) => {
        if (list.length && list[0].status === "done") {
          setPaper(list[0].paper);
          setStatus("done");
          onDone();
        }
      })
      .catch(() => {});
    return stopPolling;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleFile = async (e) => {
    const file = e.target.files[0];
    e.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file");
      return;
    }
    setError("");
    setStatus("uploading");
    try {
      const res = await uploadPaper(file);
      setPaper(res.paper);
      setStatus(res.status);
      startPolling(res.paper);
    } catch (err) {
      setStatus("");
      setError(err.message);
    }
  };

  const busy = BUSY.includes(status);

  return (
    <div style={{ background: "#1e293b", padding: 16, borderRadius: 12 }}>
      <label
        style={{
          display: "inline-block",
          padding: "10px 18px",
          borderRadius: 8,
          background: busy ? "#475569" : "#6366f1",
          color: "white",
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        {busy ? "Processing..." : "Upload research paper (PDF)"}
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFile}
          disabled={busy}
          style={{ display: "none" }}
        />
      </label>

      {paper && (
        <p style={{ margin: "12px 0 0" }}>
          Paper: <b>{paper}</b> | Status: <b>{status}</b>
        </p>
      )}
      {busy && (
        <p style={{ margin: "8px 0 0", color: "#94a3b8" }}>
          A new paper takes 2-3 minutes the first time. Please keep this page open.
        </p>
      )}
      {error && <p style={{ margin: "8px 0 0", color: "#f87171" }}>{error}</p>}
    </div>
  );
}