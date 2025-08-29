// src/front/components/OffersList.jsx
import React, { useEffect, useState } from "react";
import { ListGroup, Button, Spinner, Alert, Badge } from "react-bootstrap";

const API_BASE = import.meta.env.VITE_BACKEND_URL;

// Muestra las ofertas de una tarea.
// Props:
// - taskId: id de la tarea (obligatorio)
// - isPublisher: boolean -> si el usuario actual es el dueño de la tarea (cliente)
// - refreshSignal: cualquier valor que cambie cuando se crea/acepta/rechaza una oferta (para refetch)
export default function OffersList({ taskId, isPublisher = false, refreshSignal }) {
    const [offers, setOffers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const base = (API_BASE || "").replace(/\/+$/, "");
    const url = `${base}/api/tasks/${taskId}/offers`;

    useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                setLoading(true);
                setError("");
                const res = await fetch(url);
                const ct = res.headers.get("content-type") || "";
                if (!ct.includes("application/json")) {
                    const txt = await res.text();
                    throw new Error(`Contenido no-JSON (status ${res.status}). Preview: ${txt.slice(0, 100)}...`);
                }
                const data = await res.json();
                if (!res.ok) throw new Error(data?.message || data?.detail || `HTTP ${res.status}`);
                if (!cancelled) setOffers(Array.isArray(data) ? data : []);
            } catch (e) {
                if (!cancelled) setError(e.message || "No se pudo cargar las ofertas");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => { cancelled = true; };
    }, [url, refreshSignal]);

    const fmtMoney = (n) =>
        new Intl.NumberFormat("en-AU", { style: "currency", currency: "AUD" }).format(Number(n || 0));

    const fmtDate = (iso) => {
        if (!iso) return "";
        const d = new Date(iso);
        return Number.isNaN(d.getTime()) ? "" : d.toLocaleString();
    };

    if (loading) return <div className="mt-2"><Spinner animation="border" size="sm" /> Cargando ofertas…</div>;
    if (error) return <Alert variant="danger" className="mt-2">{error}</Alert>;

    if (offers.length === 0) {
        return <p className="text-muted mt-2">No hay ofertas todavía.</p>;
    }

    return (
        <ListGroup className="mt-2">
            {offers.map(o => (
                <ListGroup.Item key={o.id} className="d-flex align-items-center justify-content-between">
                    <div>
                        <div><strong>{fmtMoney(o.amount)}</strong> — {o.message || <em>(sin mensaje)</em>}</div>
                        <div className="text-muted small">
                            Offer #{o.id} · tasker_id: {o.tasker_id} · {fmtDate(o.created_at)}
                            {o.status && <Badge bg={o.status === "accepted" ? "success" : o.status === "rejected" ? "secondary" : "info"} className="ms-2">{o.status}</Badge>}
                        </div>
                    </div>

                    {/* Acciones SOLO para el cliente dueño de la tarea (publisher) - deja los botones por ahora como placeholder */}
                    {isPublisher && (
                        <div className="d-flex gap-2">
                            <Button size="sm" variant="success" disabled title="TODO: wire backend accept">
                                Aceptar
                            </Button>
                            <Button size="sm" variant="outline-secondary" disabled title="TODO: wire backend reject">
                                Rechazar
                            </Button>
                        </div>
                    )}
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
}