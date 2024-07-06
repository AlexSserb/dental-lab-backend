import React, { useState, useEffect } from "react";
import { Box } from "@mui/material";

const ToothMarks = ({ teethList }) => {
	const [markedTeeth, setMarkedTeeth] = useState(new Set(teethList));
	const [upperJaw, setUpperJaw] = useState([]);
	const [lowerJaw, setLowerJaw] = useState([]);

	const fillUpperJaw = () => {
		let arrUpperJaw = [];
		for (let num = 18; num >= 11; num--) {
			arrUpperJaw.push(num);
		}
		for (let num = 21; num <= 28; num++) {
			arrUpperJaw.push(num);
		}
		setUpperJaw(arrUpperJaw);
	};

	const fillLowerJaw = () => {
		let arrLowerJaw = [];
		for (let num = 48; num >= 41; num--) {
			arrLowerJaw.push(num);
		}
		for (let num = 31; num <= 38; num++) {
			arrLowerJaw.push(num);
		}
		setLowerJaw(arrLowerJaw);
	};

	useEffect(() => {
		fillUpperJaw();
		fillLowerJaw();
	}, []);


	const getToothMark = (number) => {
		const background = markedTeeth.has(number) ? "black" : "white";
		const color = markedTeeth.has(number) ? "white" : "black";

		return (
			<div style={{
				display: "flex",
				width: "25px",
				height: "25px",
				backgroundColor: background,
				color: color,
				border: "1px solid black",
				borderRadius: "50%",
				textAlign: "center"
			}}>
				<p style={{ paddingLeft: "2px" }}>
					{number}
				</p>
			</div>
		);
	};

	return (
		<Box sx={{ overflowX: "auto" }}>
			<table className="text-center">
				<tbody>
					<tr>
						{upperJaw.map(tooth => {
							return <td>{getToothMark(tooth)}</td>;
						})}
					</tr>
					<tr>
						{lowerJaw.map(tooth => {
							return <td>{getToothMark(tooth)}</td>;
						})}
					</tr>
				</tbody>
			</table>
		</Box>
	);
};

export default ToothMarks;
