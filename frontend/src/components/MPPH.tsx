import axios from "axios";
import { useEffect, useState } from "react";
import "react-date-range/dist/styles.css"; 
import "react-date-range/dist/theme/default.css"; 
import { DateRangePicker } from "react-date-range";
import Select from "react-select";

import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
} from "recharts";
import LoadingSpinner from "./LoadingSpinner";
import { Robot, host } from "../App";
import { PicksDataType } from "../types";

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
  const [picksData, setPicksData] = useState<PicksDataType | null>(null);
  const [selectionRange, setSelectionRange] = useState({
    startDate: new Date(new Date().setDate(new Date().getDate() - 365)),
    endDate: new Date(),
    key: "selection",
  });

  const [selectedInterval, setSelectedInterval] = useState(intervalOptions[1]);
  const [selectedRobot, setSelectedRobot] = useState(robotOptions[0]);
  const [selectedSite, setSelectedSite] = useState(siteOptions[0]);
  const [selectedObject, setSelectedObject] = useState(siteOptions[0]);

  // Function to fetch data
  const fetchData = (startDate: Date, endDate: Date) => {
    const lowerbound_dt = startDate.toISOString();
    const upperbound_dt = endDate.toISOString();
    axios
      .get(
        `http://${host}/picks?interval=${selectedInterval.value}&lowerbound_dt=${lowerbound_dt}&upperbound_dt=${upperbound_dt}&robot_id=${selectedRobot.value}&site=${selectedSite.value}&pick_object=${selectedObject.value}`
      )
      .then((res) => setPicksData(res.data))
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

  if (picksData != null)
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
              data={picksData.series}
              margin={{
                top: 10,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid stroke="#f5f5f5" strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis interval="preserveStartEnd" domain={[picksData.min_mpph,picksData.max_mpph]}/>

              <Line name="MPPH" type="monotone" dataKey="mpph" stroke="#00FF00" />


              {/* @ts-ignore */}
              <Tooltip content={<CustomTooltip />} />
              <Legend />
            </ComposedChart>
          </ResponsiveContainer>
          <div>
            Picks with following properties are ignored in the calculation -
            <ul>
              <li>Failed picks</li>
              <li>Picks with duration longer than 5s</li>
              <li>Picks with duration less than 1s</li>
            </ul>
          </div>
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
        <p>MPPH: {payload[0].payload.mpph}</p>
        <p>Total Duration: {payload[0].payload.total_duration}s</p>
        <p>Total Picks: {payload[0].payload.total_picks}</p>
      </div>
    );
  }

  return null;
};
