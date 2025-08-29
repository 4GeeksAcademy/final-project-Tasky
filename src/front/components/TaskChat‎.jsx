import React, { useEffect, useRef, useState } from "react";
import { Alert, Button, Form, InputGroup, ListGroup, Spinner } from "react-bootstrap";

const API_BASE = import.meta.env.VITE_BACKEND_URL;
const REFRESH_MS = 3000; // auto-refresh cada 3 segundos

/**
 * Chat por tarea (auto-refresh, sin botón de actualizar)
 * Props:
 *  - taskId
 *  - user: { id, role } | null
 *  - demo: boolean  // si true, usa mensajes en duro y simula POST
 */
export default function TaskChat({ taskId, user, demo = false }) {
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sending, setSending] = useState(false);
    const [error, setError] = useState("");
    const [text, setText] = useState("");
    const [lastUpdated, setLastUpdated] = useState(null);

    const pollRef = useRef(null);
    const listEndRef = useRef(null);

    const scrollToEnd = () => listEndRef.current?.scrollIntoView({ behavior: "smooth" });

    useEffect(() => {
        // Carga inicial + auto-refresh
        refreshMessages();
        pollRef.current = setInterval(() => refreshMessages({ silent: true }), REFRESH_MS);
        return () => pollRef.current && clearInterval(pollRef.current);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [taskId, demo]);

    useEffect(() => {
        scrollToEnd();
    }, [messages]);

    const refreshMessages = async ({ silent = false } = {}) => {
        if (!silent) { setLoading(true); setError(""); }
        try {
            if (demo) {
                // Mensajes dummy
                const t = Date.now();
                const me = user?.id ?? 10;
                const other = 999;
                const demoMsgs = [
                    { id: 1, body: "Hola, ¿cuándo podrías venir?", created_at: new Date(t - 1000 * 60 * 25).toISOString(), sender_id: other },
                    { id: 2, body: "Hoy en la tarde puedo.", created_at: new Date(t - 1000 * 60 * 23).toISOString(), sender_id: me },
                    { id: 3, body: "Súper, gracias.", created_at: new Date(t - 1000 * 60 * 21).toISOString(), sender_id: other },
                ];
                await new Promise(r => setTimeout(r, 250));
                setMessages(demoMsgs);
                setLastUpdated(new Date());
                return;
            }

            // Real GET
            const base = (API_BASE || "").replace(/\/+$/, "");
            const url = `${base}/api/tasks/${taskId}/messages`;
            const res = await fetch(url);
            const ct = res.headers.get("content-type") || "";
            if (!ct.includes("application/json")) {
                const txt = await res.text();
                throw new Error(`No-JSON (status ${res.status}) en ${url}. Preview: ${txt.slice(0, 120)}...`);
            }
            const data = await res.json();
            if (!res.ok) throw new Error(data?.message || data?.detail || `HTTP ${res.status}`);
            setMessages(Array.isArray(data) ? data : []);
            setLastUpdated(new Date());
        } catch (err) {
            setError(err.message || "No se pudieron cargar los mensajes");
        } finally {
            if (!silent) setLoading(false);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        const textTrim = text.trim();
        if (!textTrim) return;
        setSending(true);
        setError("");

        try {
            if (demo) {
                // Simula POST agregando al hilo
                await new Promise(r => setTimeout(r, 200));
                const newMsg = {
                    id: Math.floor(Math.random() * 100000),
                    body: textTrim,
                    created_at: new Date().toISOString(),
                    sender_id: user?.id ?? 10,
                };
                setMessages(prev => [...prev, newMsg]);
                setText("");
                setLastUpdated(new Date());
                return;
            }

            // Real POST
            const base = (API_BASE || "").replace(/\/+$/, "");
            const url = `${base}/api/tasks/${taskId}/messages`;
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                // credentials: "include", // si usas cookies de sesión
                body: JSON.stringify({ body: textTrim }),
            });
            const ct = res.headers.get("content-type") || "";
            const payload = ct.includes("application/json") ? await res.json() : await res.text();
            if (!res.ok) {
                const msg = typeof payload === "string" ? `HTTP ${res.status}: ${payload.slice(0, 120)}` :
                    (payload?.message || payload?.detail || `HTTP ${res.status}`);
                throw new Error(msg);
            }
            if (payload && payload.id) {
                setMessages(prev => [...prev, payload]);
            } else {
                await refreshMessages({ silent: true });
            }
            setText("");
            setLastUpdated(new Date());
        } catch (err) {
            setError(err.message || "No se pudo enviar el mensaje");
        } finally {
            setSending(false);
        }
    };

    const formatDate = (iso) => {
        const d = new Date(iso);
        return isNaN(d.getTime()) ? "" : d.toLocaleString();
    };

    return (
        <div>
            {/* Info auto-refresh */}
            <div className="small text-muted mb-2">
                Auto-actualizado {REFRESH_MS / 1000}s
                {lastUpdated ? ` · Última: ${formatDate(lastUpdated.toISOString())}` : ""}
            </div>

            {loading ? (
                <Spinner animation="border" />
            ) : error ? (
                <Alert variant="danger">{error}</Alert>
            ) : (
                <>
                    {/* Lista de mensajes */}
                    <div style={{ maxHeight: 350, overflowY: "auto", border: "1px solid #eee", borderRadius: 8, padding: 8 }}>
                        <ListGroup variant="flush">
                            {messages.map((m) => {
                                const me = user && m.sender_id === user.id;
                                return (
                                    <ListGroup.Item
                                        key={m.id}
                                        className={`d-flex ${me ? "justify-content-end" : "justify-content-start"}`}
                                        style={{ border: "none" }}
                                    >
                                        <div
                                            style={{
                                                maxWidth: "75%",
                                                borderRadius: 12,
                                                padding: "6px 10px",
                                                background: me ? "#e7f1ff" : "#f5f5f5",
                                            }}
                                        >
                                            <div className="small text-muted mb-1">
                                                {me ? "Tú" : "Otro"} · {formatDate(m.created_at)}
                                            </div>
                                            <div style={{ whiteSpace: "pre-wrap" }}>{m.body}</div>
                                        </div>
                                    </ListGroup.Item>
                                );
                            })}
                            <div ref={listEndRef} />
                        </ListGroup>
                    </div>

                    {/* Input para enviar */}
                    <Form onSubmit={handleSend} className="mt-2">
                        <InputGroup>
                            <Form.Control
                                placeholder="Escribe un mensaje..."
                                value={text}
                                onChange={(e) => setText(e.target.value)}
                                disabled={sending}
                            />
                            <Button type="submit" variant="primary" disabled={sending || !text.trim()}>
                                {sending ? "Enviando..." : "Enviar"}
                            </Button>
                        </InputGroup>
                    </Form>
                </>
            )}
        </div>
    );
}