// src/front/components/SendOfferModal.jsx
import React, { useState } from "react";
import { Modal, Button, Form, Alert, InputGroup } from "react-bootstrap";
import { useStore } from "../hooks/useGlobalReducer";

const API_BASE = import.meta.env.VITE_BACKEND_URL;

export default function SendOfferModal({ show, onHide, taskId, onCreated }) {
    const { store } = useStore();
    const user = store?.user; // usuario “logueado” (mock o real)

    const [amount, setAmount] = useState("");
    const [message, setMessage] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    const reset = () => {
        setAmount("");
        setMessage("");
        setError("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");

        try {
            if (!user?.id) {
                throw new Error("No hay usuario (tasker) en sesión");
            }

            // Soporta coma decimal y valida monto > 0
            const nAmount = Number(String(amount).replace(",", "."));
            if (!Number.isFinite(nAmount) || nAmount <= 0) {
                throw new Error("Monto inválido");
            }

            const base = (API_BASE || "").replace(/\/+$/, "");
            const url = `${base}/api/tasks/${taskId}/offers`;

            // (Logs útiles mientras desarrollas; puedes quitarlos al final)
            console.log("POST →", url, {
                tasker_id: user.id,
                amount: nAmount,
                message: message.trim(),
            });

            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tasker_id: user.id,
                    amount: nAmount,
                    message: message.trim(),
                }),
            });

            const ct = res.headers.get("content-type") || "";
            const raw = await res.text();
            // (Log para depurar respuestas no-JSON)
            console.log("Status:", res.status, "CT:", ct, "Raw:", raw);

            const payload = ct.includes("application/json") ? JSON.parse(raw) : raw;

            if (!res.ok) {
                const msg =
                    typeof payload === "string"
                        ? `HTTP ${res.status}: ${payload.slice(0, 200)}`
                        : payload?.message || payload?.detail || `HTTP ${res.status}`;
                throw new Error(msg);
            }

            onCreated?.(payload);
            reset();
            onHide?.();
        } catch (err) {
            console.error("POST failed:", err);
            setError(err.message || "No se pudo enviar la oferta");
        } finally {
            setSubmitting(false);
        }
    };

    const canSubmit =
        !submitting &&
        !!user?.id &&
        amount !== "" &&
        Number(String(amount).replace(",", ".")) > 0 &&
        message.trim().length > 0;

    return (
        <Modal show={show} onHide={onHide} centered>
            <Form onSubmit={handleSubmit}>
                <Modal.Header closeButton>
                    <Modal.Title>Enviar oferta</Modal.Title>
                </Modal.Header>

                <Modal.Body>
                    {error && (
                        <Alert variant="danger" className="mb-3">
                            {error}
                        </Alert>
                    )}

                    {!user?.id && (
                        <Alert variant="warning" className="mb-3">
                            No hay usuario en sesión. Haz un{" "}
                            <code>LOGIN</code> demo en tu store para probar.
                        </Alert>
                    )}

                    <Form.Group className="mb-3">
                        <Form.Label>Monto</Form.Label>
                        <InputGroup>
                            <InputGroup.Text>$</InputGroup.Text>
                            <Form.Control
                                type="number"
                                min="0"
                                step="0.01"
                                value={amount}
                                onChange={(e) => setAmount(e.target.value)}
                                placeholder="Tu oferta"
                                required
                                disabled={submitting}
                            />
                        </InputGroup>
                    </Form.Group>

                    <Form.Group className="mb-2">
                        <Form.Label>Mensaje</Form.Label>
                        <Form.Control
                            as="textarea"
                            rows={3}
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Nota breve"
                            required
                            disabled={submitting}
                        />
                    </Form.Group>

                    {user?.id && (
                        <div className="small text-muted">
                            Se enviará como <strong>tasker #{user.id}</strong>.
                        </div>
                    )}
                </Modal.Body>

                <Modal.Footer>
                    <Button variant="secondary" onClick={onHide} disabled={submitting}>
                        Cancelar
                    </Button>
                    <Button type="submit" variant="primary" disabled={!canSubmit}>
                        {submitting ? "Enviando..." : "Enviar oferta"}
                    </Button>
                </Modal.Footer>
            </Form>
        </Modal>
    );
}
