import { useEffect, useState } from "react";

import Sync from "./components/Sync";
import Tonnes from "./components/Tonnes";
import Picks from "./components/Picks";
import Boxes from "./components/Boxes";
import Hours from "./components/Hours";
import MPPH from "./components/MPPH";
import LoadingSpinner from "./components/LoadingSpinner";
import axios from "axios";

export type Robot = {
  id: string;
  name: string;
};
export const host = `${window.location.hostname}:5001`;
export default function App() {
  // State to keep track of the active tab
  const [activeTab, setActiveTab] = useState("sync");
  const [robots, setRobots] = useState<Robot[] | null>(null);
  const [sites, setSites] = useState<string[] | null>(null);
  const [objects, setObjects] = useState<string[] | null>(null);

  // Fetch robots
  function fetchRobots() {
    axios
      .get(`http://${host}/robots`)
      .then((res) => setRobots(res.data?.robots))
      .catch((err) => console.error("Error Fetching Robots: " + err));
  }
  // Fetch sites
  function fetchSites() {
    axios
      .get(`http://${host}/sites`)
      .then((res) => setSites(res.data?.sites))
      .catch((err) => console.error("Error Fetching Sites: " + err));
  }
  //Fetch Pick Objects
  function fetchObjects() {
    axios
      .get(`http://${host}/objects`)
      .then((res) => setObjects(res.data?.objects))
      .catch((err) => console.error("Error Fetching Objects: " + err));
  }
  useEffect(() => {
    fetchRobots();
    fetchSites();
    fetchObjects();
  }, []);
  // Determine if the component should be displayed based on the active tab
  const getDisplayStyle = (tabName: string) => {
    return activeTab === tabName ? "block" : "none";
  };
  if (robots && sites && objects) {
    return (
      <div className="p-4">
        {/* Tab navigation */}
        <div className="flex space-x-4 mb-4">
          <button
            className={`px-4 py-2 ${
              activeTab === "sync" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("sync")}
          >
            Sync
          </button>
          <button
            className={`px-4 py-2 ${
              activeTab === "tonnes" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("tonnes")}
          >
            Tonnes
          </button>
          <button
            className={`px-4 py-2 ${
              activeTab === "picks" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("picks")}
          >
            Picks
          </button>
          <button
            className={`px-4 py-2 ${
              activeTab === "boxes" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("boxes")}
          >
            Boxes
          </button>
          <button
            className={`px-4 py-2 ${
              activeTab === "hours" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("hours")}
          >
            Hours
          </button>
          <button
            className={`px-4 py-2 ${
              activeTab === "mpph" ? "text-blue-500" : ""
            }`}
            onClick={() => setActiveTab("mpph")}
          >
            MPPH
          </button>
        </div>

        {/* Content area for the components */}
        <div className="content-area">
          <div style={{ display: getDisplayStyle("sync") }}>
            <Sync />
          </div>
          <div style={{ display: getDisplayStyle("tonnes") }}>
            <Tonnes robots={robots} sites={sites} objects={objects} />
          </div>
          <div style={{ display: getDisplayStyle("picks") }}>
            <Picks robots={robots} sites={sites} objects={objects} />
          </div>
          <div style={{ display: getDisplayStyle("boxes") }}>
            <Boxes robots={robots} sites={sites} objects={objects} />
          </div>
          <div style={{ display: getDisplayStyle("hours") }}>
            <Hours robots={robots} sites={sites} objects={objects} />
          </div>
          <div style={{ display: getDisplayStyle("mpph") }}>
            <MPPH robots={robots} sites={sites} objects={objects} />
          </div>
        </div>
      </div>
    );
  } else return <LoadingSpinner />;
}
