import axios from "axios";
import { useEffect, useState } from "react";
import "react-date-range/dist/styles.css"; 
import "react-date-range/dist/theme/default.css"; 
import { DateRangePicker } from "react-date-range";
import Select from "react-select";

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  Bar,
} from "recharts";
import LoadingSpinner from "./LoadingSpinner";
import { Robot, host } from "../App";
import { TasksDataType } from "../types";

const intervalOptions = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

export default function ({
  robots,
  sites,
  objects,
}: {
  robots: Robot[];
  sites: string[];
  objects: string[];
}) {
  let robotOptions = [
    { value: "all", label: "All Robots" },
    ...robots.map((r) => {
      return {
        value: r.id,
        label: r.name,
      };
    }),
  ];
  let siteOptions = [
    { value: "all", label: "All Sites" },
    ...sites.map((s) => {
      return {
        value: s,
        label: s,
      };
    }),
  ];
  let pickObjectOptions = [
    { value: "all", label: "All Objects" },
    ...objects.map((p) => {
      return {
        value: p,
        label: p,
      };
    }),
  ];
  const [tasksData, setTasksData] = useState<TasksDataType | null>(null);
  const [selectionRange, setSelectionRange] = useState({
    startDate: new Date(new Date().setDate(new Date().getDate() - 7)),
    endDate: new Date(),
    key: "selection",
  });

  const [selectedInterval, setSelectedInterval] = useState(intervalOptions[0]);
  const [selectedRobot, setSelectedRobot] = useState(robotOptions[0]);
  const [selectedSite, setSelectedSite] = useState(siteOptions[0]);
  const [selectedObject, setSelectedObject] = useState(siteOptions[0]);

  // Function to fetch data
  const fetchData = (startDate: Date, endDate: Date) => {
    const lowerbound_dt = startDate.toISOString();
    const upperbound_dt = endDate.toISOString();
    axios
      .get(
        `http://${host}/tasks?interval=${selectedInterval.value}&lowerbound_dt=${lowerbound_dt}&upperbound_dt=${upperbound_dt}&robot_id=${selectedRobot.value}&site=${selectedSite.value}&pick_object=${selectedObject.value}`
      )
      .then((res) => setTasksData(res.data))
      .catch((error) => console.error("Error fetching data:", error));
  };

  useEffect(() => {
    fetchData(selectionRange.startDate, selectionRange.endDate);
  }, [
    selectionRange,
    selectedInterval,
    selectedRobot,
    selectedSite,
    selectedObject,
  ]);

  function handleSelect(ranges: any) {
    const { selection } = ranges;
    setSelectionRange(selection);
  }

  if (tasksData != null)
    return (
      <div>
        <div className="lg:grid lg:grid-cols-2">
          <DateRangePicker ranges={[selectionRange]} onChange={handleSelect} />
          <div>
            <label className="mt-2 block text-sm text-blue-700">
              Interval
              <Select
                defaultValue={selectedInterval}
                //@ts-ignore
                onChange={setSelectedInterval}
                options={intervalOptions}
              />
            </label>
            <label className="mt-2 block text-sm text-blue-700">
              Robot
              <Select
                defaultValue={selectedRobot}
                //@ts-ignore
                onChange={setSelectedRobot}
                options={robotOptions}
              />
            </label>
            <label className="mt-2 block text-sm text-blue-700">
              Site
              <Select
                defaultValue={selectedSite}
                //@ts-ignore
                onChange={setSelectedSite}
                options={siteOptions}
              />
            </label>
            <label className="mt-2 block text-sm text-blue-700">
              Pick Object
              <Select
                defaultValue={selectedObject}
                //@ts-ignore
                onChange={setSelectedObject}
                options={pickObjectOptions}
              />
            </label>
          </div>
        </div>
        <div className="h-[50vh]">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              width={500}
              height={400}
              data={tasksData.series}
              margin={{
                top: 10,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid stroke="#f5f5f5" strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis interval="preserveStartEnd" />

              <Area
              name="Accumulated Operation Hours"
                type="monotone"
                dataKey="accumulating_total_duration"
                fill="#8884d8"
                stroke="#8884d8"
              />
              <Bar name="Operation Hours" dataKey="total_duration" barSize={20} fill="#413ea0" />
              <Bar name="Picks Duration" dataKey="total_successful_picks_duration" barSize={20} fill="#ff0000" />

              {/* @ts-ignore */}
              <Tooltip content={<CustomTooltip />} />
              <Legend />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  else return <LoadingSpinner />;
}
// Custom Tooltip Component
//@ts-ignore
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-2 border border-gray-200 shadow rounded">
        <p>Date: {payload[0].payload.date}</p>
        <p>Accum Op Hours: {(payload[0].payload.total_duration/3600).toFixed(2)} h</p>
        <p>Op Hours: {(payload[0].payload.total_duration/3600).toFixed(2)} h</p>
        <p>Picks Duration: {(payload[0].payload.total_successful_picks_duration/3600).toFixed(2)} h</p>
      </div>
    );
  }

  return null;
};
