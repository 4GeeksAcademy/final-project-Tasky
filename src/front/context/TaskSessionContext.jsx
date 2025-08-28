import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

const TaskSessionContext = createContext(null);
const API_BASE = import.meta.env.VITE_BACKEND_URL;

export function TaskSessionProvider({ task, currentUser, children }) {
    const base = (API_BASE || "").replace(/\/+$/, "");
    const taskId = task?.id ?? null;

    const [deal, setDeal] = useState(null);
    const [dealLoading, setDealLoading] = useState(false);
    const [dealError, setDealError] = useState("");

    // Carga el último deal de la task (si existe)
    useEffect(() => {
        let cancelled = false;
        async function load() {
            setDealError(""); setDeal(null);
            if (!taskId) return;
            setDealLoading(true);
            try {
                const res = await fetch(`${base}/api/tasks/${taskId}/deal`);
                if (res.status === 404) { if (!cancelled) setDeal(null); return; }
                const ct = res.headers.get("content-type") || "";
                const raw = ct.includes("application/json") ? await res.json() : await res.text();
                if (!res.ok) throw new Error(typeof raw === "string" ? raw : (raw?.message || `HTTP ${res.status}`));
                if (!cancelled) setDeal(raw);
            } catch (e) {
                if (!cancelled) setDealError(e.message || "No se pudo cargar el deal");
            } finally {
                if (!cancelled) setDealLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, [taskId, base]);

    const value = useMemo(() => {
        const assignedTaskerId =
            task?.assigned_tasker_id ?? deal?.tasker_id ?? null;

        const publisherId =
            task?.publisher_id ?? task?.client_id ?? deal?.client_id ?? null;

        const dealId = deal?.id ?? task?.deal_id ?? task?.task_dealed_id ?? null;

        const isPublisher = !!currentUser && publisherId === currentUser?.id;

        const canReviewTasker =
            task?.status === "completed" &&
            currentUser?.role === "client" &&
            publisherId === currentUser?.id &&
            !!assignedTaskerId;

        const canChat =
            ["assigned", "in_progress", "completed"].includes(task?.status) &&
            !!currentUser &&
            (task?.client_id === currentUser.id || assignedTaskerId === currentUser.id);

        const canSendOffer =
            !!currentUser && currentUser.role === "tasker" && task?.publisher_id !== currentUser.id;

        return {
            task,
            currentUser,
            taskId,
            publisherId,
            assignedTaskerId,
            deal,
            dealId,
            dealLoading,
            dealError,
            isPublisher,
            canReviewTasker,
            canChat,
            canSendOffer,
        };
    }, [task, currentUser, deal]);

    return (
        <TaskSessionContext.Provider value={value}>
            {children}
        </TaskSessionContext.Provider>
    );
}

export function useTaskSession() {
    return useContext(TaskSessionContext);
}
