import axios from "axios";
import { useEffect, useState } from "react";
import DestinationComponent, { Destination } from "./Destination";
import { host } from "../App";

export default function () {
  const [syncDestinations, setSyncDestinations] = useState<
    Destination[] | null
  >(null);

  const fetchDestinations = () => {
    axios
      .get(`http://${host}/destinations`)
      .then((res) => setSyncDestinations(res.data))
      .catch((error) => console.error("Error fetching data:", error));
  };
  useEffect(() => {
    fetchDestinations();
  }, []);

  return (
    <div className="relative overflow-x-auto">
      <table className="w-full text-sm text-left rtl:text-right">
        <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
          <tr>
            <th className="px-6 py-3">Name</th>
            <th className="px-6 py-3">Address</th>
            <th className="px-6 py-3">Action</th>
            <th className="px-6 py-3">Last Sync</th>
          </tr>
        </thead>
        <tbody>
          {syncDestinations?.map((des) => (
            <DestinationComponent key={des.robot_id} destination={des} reload={fetchDestinations} />
          ))}
        </tbody>
      </table>
    </div>
  );
}
