import { useState } from "react";
import { DateRangePicker } from "react-date-range";

const [selectionRange, setSelectionRange] = useState({
    startDate: new Date(new Date().setDate(new Date().getDate() - 7)),
    endDate: new Date(),
    key: "selection",
  });

function handleSelect(ranges: any) {
    const { selection } = ranges;
    setSelectionRange(selection);
  }

export default function () {
    return (
      <DateRangePicker ranges={[selectionRange]} onChange={handleSelect} />
    );
  };
  