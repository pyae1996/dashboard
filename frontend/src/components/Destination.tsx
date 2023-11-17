import axios from "axios";
import { useState } from "react";
import LoadingSpinner from "./LoadingSpinner";
import { host } from "../App";
export type Destination = {
  robot_id: string;
  name: string;
  address: string;
  last_sync: string;
};
export default function ({
  destination,
  reload,
}: {
  destination: Destination;
  reload: () => void;
}) {
  const [loading, setLoading] = useState<boolean>(false);
  const [syncSuccess, setSyncSuccess] = useState<boolean | null>(null);

  function handleSync(des: Destination) {
    setLoading(true);
    axios
      .get(
        `http://${host}/sync?robot_id=${des.robot_id}&address=${des.address}`
      )
      .then((res) => res.status == 200 && setSyncSuccess(true))
      .catch(() => setSyncSuccess(false))
      .finally(() => {
        setLoading(false);
        reload();
      });
  }

  return (
    <tr key={destination.robot_id} className="bg-gray-300">
      <td className="px-6 py-4">{destination.name}</td>
      <td className="px-6 py-4">{destination.address}</td>
      <td className="px-6 py-4 flex items-center">
        <button
          onClick={() => handleSync(destination)}
          className="bg-gray-200 p-2 shadow-md rounded-full hover:bg-green-100"
        >
          Sync
        </button>
        {loading && <LoadingSpinner />}
        {syncSuccess ? (
          <span className="ml-2 text-green-600">Success</span>
        ) : (
          syncSuccess != null && <span className="text-red-500">Offline</span>
        )}
      </td>
      <td className="px-6 py-4">{destination.last_sync || "Never"}</td>
    </tr>
  );
}
