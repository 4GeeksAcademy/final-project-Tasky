
// src/front/pages/TaskDetail.jsx
import React, { useEffect, useState, useRef } from "react";
import { useParams, Link, useLocation } from "react-router-dom";
import { Spinner, Alert, Container, Row, Col, Card, Badge, Button, Tabs, Tab } from "react-bootstrap";
import SendOfferModal from "../components/SendOfferModal";
import ReviewTaskerModal from "../components/ReviewTaskerModal";
import TaskChat from "../components/TaskChat";
import { useStore } from "../hooks/useGlobalReducer"; // <- leemos user del store global
import { TaskSessionProvider } from "../context/TaskSessionContext";

const API_BASE = import.meta.env.VITE_BACKEND_URL;

/**
 * Props:
 *  - user: { id, role } | null   // opcional; si no viene, usamos el user del store
 *  - demo: boolean                // si true, mostramos Chat/Review/Offer con dummy data forzada
 */
export default function TaskDetail({ user, demo = true }) {
    const { store } = useStore();
    const storeUser = store?.user;                    // usuario “logueado” (mock o real)
    const inputUser = user ?? storeUser;              // prioriza prop; si no, usa store

    const { taskId } = useParams();
    const [task, setTask] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [offers, setOffers] = useState([]);

    const location = useLocation();
    const qs = new URLSearchParams(location.search);
    const qsOpenReview = qs.get("openReview") === "1";
    const qsTaskerId = qs.get("taskerId");   // ej: ?taskerId=1
    const qsDealId = qs.get("dealId");       // ej: ?dealId=2

    // Modals
    const [showOfferModal, setShowOfferModal] = useState(false);
    const [showReviewModal, setShowReviewModal] = useState(false);

    // Flash
    const [flash, setFlash] = useState("");

    useEffect(() => {
        const fetchTask = async () => {
            setLoading(true);
            setError("");
            try {
                const base = (API_BASE || "").replace(/\/+$/, "");
                const url = `${base}/api/tasks/${taskId}`;
                const res = await fetch(url);
                const ct = res.headers.get("content-type") || "";
                if (!ct.includes("application/json")) {
                    const text = await res.text();
                    throw new Error(
                        `La API devolvió contenido no-JSON (status ${res.status}). URL: ${url}\nPreview: ${text.slice(0, 120)}...`
                    );
                }
                const data = await res.json();
                if (!res.ok) throw new Error(data?.message || data?.detail || `HTTP ${res.status}`);
                setTask(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };
        fetchTask();
    }, [taskId]);

    // Auto-abrir el modal de review si la URL trae ?openReview=1 (una sola vez, cuando termine de cargar)
    const autoOpenedRef = useRef(false);
    useEffect(() => {
        if (!loading && qsOpenReview && !autoOpenedRef.current) {
            setShowReviewModal(true);
            autoOpenedRef.current = true;
        }
    }, [loading, qsOpenReview]);

    const handleOfferCreated = (created) => {
        setFlash("¡Oferta enviada con éxito!");
        setOffers(prev => [created, ...prev]);
    };
    const handleReviewCreated = () => setFlash("¡Calificación enviada con éxito!");

    if (loading) return <Spinner animation="border" />;
    if (error) return <Alert variant="danger" className="mt-3">{error}</Alert>;
    if (!task) return <Alert variant="warning">Tarea no encontrada</Alert>;

    // === DEMO: tarea “lista para chat/calificación”
    const effectiveUser = demo ? (inputUser || { id: 10, role: "client" }) : inputUser;
    const effectiveTask = demo
        ? {
            ...task,
            status: "completed",                    // habilita chat/calificación en demo
            client_id: task.client_id || (effectiveUser?.role === "client" ? effectiveUser?.id : 10),
            assigned_tasker_id: task.assigned_tasker_id || 99,
        }
        : task;

    // Reglas reales (solo se aplican cuando demo=false)
    const canReviewTasker = demo
        ? true
        : (
            effectiveTask?.status === "completed" &&           // tarea finalizada
            effectiveUser?.role === "client" &&                // el que califica es cliente
            effectiveTask?.client_id === effectiveUser?.id &&  // es el dueño de la tarea
            !!effectiveTask?.assigned_tasker_id                // existe tasker asignado
        );

    const canChat = demo
        ? true // <— EN DEMO: siempre muestra el tab Chat
        : (
            ["assigned", "in_progress", "completed"].includes(effectiveTask?.status) &&
            effectiveUser &&
            (
                effectiveTask?.client_id === effectiveUser.id ||
                effectiveTask?.assigned_tasker_id === effectiveUser.id
            )
        );

    // Mostrar botón "Enviar oferta":
    // - En DEMO: siempre visible para que puedas mostrar el flujo.
    // - En real: solo si hay user tasker y no es el publisher de la tarea.
    const canSendOffer = demo
        ? true
        : (!!inputUser && inputUser.role === "tasker" && effectiveTask.publisher_id !== inputUser.id);

    return (
        <TaskSessionProvider task={effectiveTask} currentUser={effectiveUser}>
            <Container className="py-4">
                {demo && (
                    <Alert variant="warning" className="mb-3">
                        DEMO MODE: datos forzados para mostrar flujos (Chat/Review/Offer)
                    </Alert>
                )}
                {flash && (
                    <Alert variant="success" onClose={() => setFlash("")} dismissible className="mb-3">
                        {flash}
                    </Alert>
                )}

                <Row className="mb-3">
                    <Col>
                        <h1>{effectiveTask.title}</h1>
                        {effectiveTask.status && <Badge bg="info">{effectiveTask.status}</Badge>}
                    </Col>
                </Row>

                <Row>
                    {/* Izquierda: Tabs */}
                    <Col md={8}>
                        <Tabs defaultActiveKey="detalle" className="mb-3" fill>
                            <Tab eventKey="detalle" title="Detalle">
                                <Card className="mb-3">
                                    <Card.Header>Descripción</Card.Header>
                                    <Card.Body>
                                        <p>{effectiveTask.description || "Sin descripción"}</p>
                                    </Card.Body>
                                </Card>
                            </Tab>

                            {canChat && (
                                <Tab eventKey="chat" title="Chat">
                                    <Card className="mb-3">
                                        <Card.Header>Mensajes de la tarea</Card.Header>
                                        <Card.Body>
                                            <TaskChat taskId={effectiveTask.id} user={effectiveUser} demo={demo} />
                                        </Card.Body>
                                    </Card>
                                </Tab>
                            )}
                        </Tabs>
                    </Col>

                    {/* Derecha: Detalles + botones */}
                    <Col md={4}>
                        <Card className="mb-3">
                            <Card.Header>Detalles</Card.Header>
                            <Card.Body>
                                {effectiveTask.price && <p><strong>Precio:</strong> ${effectiveTask.price}</p>}
                                {effectiveTask.location && <p><strong>Ubicación:</strong> {effectiveTask.location}</p>}
                                <p><strong>Publicado por:</strong> {effectiveTask.publisher_id}</p>
                                <Link to={`/u/${effectiveTask.publisher_id}`}>Ver perfil</Link>
                                {effectiveTask.assigned_tasker_id && (
                                    <p className="mt-2"><strong>Tasker asignado:</strong> {effectiveTask.assigned_tasker_id}</p>
                                )}
                            </Card.Body>
                        </Card>

                        {/* Oferta (demo o real) */}
                        {canSendOffer && (
                            <Button variant="primary" className="me-2 mb-2" onClick={() => setShowOfferModal(true)}>
                                Enviar oferta
                            </Button>
                        )}

                        {/* Calificar (en demo se muestra siempre) */}
                        {canReviewTasker && (
                            <Button variant="success" className="mb-2" onClick={() => setShowReviewModal(true)}>
                                Calificar tasker
                            </Button>
                        )}
                    </Col>
                </Row>

                {/* Modales */}
                <SendOfferModal
                    show={showOfferModal}
                    onHide={() => setShowOfferModal(false)}
                    taskId={effectiveTask.id}
                    onCreated={handleOfferCreated}
                    demo={demo}  // el modal leerá user del store para enviar tasker_id
                />

                <ReviewTaskerModal
                    show={showReviewModal}
                    onHide={() => setShowReviewModal(false)}
                    taskId={effectiveTask.id}
                    taskerId={Number(qsTaskerId) || effectiveTask.assigned_tasker_id}
                    dealId={qsDealId ? Number(qsDealId) : undefined}
                    onCreated={handleReviewCreated}
                    demo={false}
                />
            </Container>
        </TaskSessionProvider>
    );
}
