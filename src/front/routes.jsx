// src/front/routes.jsx
import React from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

// Only the pages you want RIGHT NOW
import Layout from "./pages/Layout";
import Home from "./pages/Home";
import Login from "./pages/Login";
import TaskDetail from "./pages/TaskDetail";


// === DEMO SWITCHES (pon en false cuando conectes backend real) ===
const DEMO = true;
const DEMO_USER = { id: 10, role: "client" }; // cliente demo

export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/login", element: <Login /> },
      { path: "/tasks/:taskId", element: <TaskDetail user={DEMO ? DEMO_USER : null} demo={DEMO} /> },
      // Catch-all so bad routes don’t crash
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
