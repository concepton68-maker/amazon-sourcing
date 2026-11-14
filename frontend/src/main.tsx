import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
// Polices servies par le site lui-même (aucun appel à Google Fonts)
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/manrope/700.css";
import "@fontsource/manrope/800.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/ibm-plex-mono/600.css";
import "./styles.css";

createRoot(document.getElementById("racine")!).render(<StrictMode><App /></StrictMode>);
