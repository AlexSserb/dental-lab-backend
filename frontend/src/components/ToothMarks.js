import React, { useState, useEffect } from 'react';


const ToothMarks = ({ teethList }) => {
  const [ teeth, setTeeth ] = useState(teethList);
	const [ teethNumbers, setTeethNumbers ] = useState([8,7,6,5,4,3,2,1,1,2,3,4,5,6,7,8]);
	const [ upperJaw, setUpperJaw ] = useState([]);
	const [ lowerJaw, setLowerJaw ] = useState([]);

  useEffect(() => {
		let arrUpperJaw = Array(16).fill(false);
		let arrLowerJaw = Array(16).fill(false);

		for (let i = 0; i < teeth.length; i++) {
			let toothIndex = teeth[i].tooth_number - 1;

			if (teeth[i].is_right_side) {
				toothIndex = 8 - toothIndex;
			}
			if (!teeth[i].is_right_side) {
				toothIndex = 8 + toothIndex;
			}

			if (teeth[i].is_upper_jaw) arrUpperJaw[toothIndex] = true;
			else arrLowerJaw[toothIndex] = true;
		}

		setLowerJaw(arrLowerJaw);
		setUpperJaw(arrUpperJaw);
  }, []);


	const getToothMark = (isMarked) => {
		let background = isMarked ? "black" : "white";

		return (
			<div style={{
				display: "flex",
				width: "20px",
				height: "20px",
				backgroundColor: background,
				border: '1px solid black',
				borderRadius: "50%"
			}}>
			</div>
		)
	}

  return (
    <div>
			<table className="text-center"> 
        <thead> 
          <tr> 
						{ teethNumbers.map(number => {
							return <th class="p-1">{number}</th>
						})}
          </tr> 
        </thead> 
        <tbody> 
          <tr>
						{ upperJaw.map(tooth => {
							return <td>{getToothMark(tooth)}</td>
						})}
					</tr>
					<tr>
						{ lowerJaw.map(tooth => {
							return <td>{getToothMark(tooth)}</td>
						})}
					</tr>
        </tbody> 
      </table> 
    </div>
  )
}

export default ToothMarks;
