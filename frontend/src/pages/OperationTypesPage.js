import React, { useContext, useState, useEffect } from "react";
import { Table } from "reactstrap";
import Button from '@mui/material/Button';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import { useNavigate } from 'react-router-dom';

import AuthContext from "../context/AuthContext";
import operationTypesService from "../servicies/OperationTypesService";
import OperationTypesModal from "../components/OperationTypesModal";

const OperationTypesPage = () => {
  let [ operTypesList, setOperTypesList ] = useState([]);
	let [ activeItem, setActiveItem ] = useState({});
	let [ modal, setModal ] = useState(false);
  let { authTokens } = useContext(AuthContext);
  let navigate = useNavigate();

	const refreshList = (accessToken) => {
    operationTypesService.getAll(accessToken)
      .then(res => {
        setOperTypesList(res.data);
      })
      .catch(err => console.log(err));
  }

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
		refreshList(authTokens.access);
  }, [authTokens])

	const createItem = () => {
		setModal(!modal);
	}

	const editItem = (item) => {
		setActiveItem(item);
		setModal(!modal);
	}

	const handleDelete = (item) => {
		if (!authTokens) {
			navigate('/login');
			return;
		}
		operationTypesService.deleteOperType(item, authTokens.access)
			.then(() => refreshList(authTokens.access))
			.catch(err => console.log(err));
	}

	// Submit an item
	const handleSubmit = item => {
		toggle();
		if (!authTokens) {
			navigate('/login');
			return;
		}
		if (item.id) {
			// if old post to edit and submit
			operationTypesService.putOperType(item, authTokens.access)
				.then(() => refreshList(authTokens.access))
				.catch(err => console.log(err));
			return;
		}
		// if new post to submit
		operationTypesService.postOperType(item, authTokens.access)
			.then(() => refreshList(authTokens.access))
			.catch(err => console.log(err));
	}

	// Main variable to render items on the screen
  const renderItems = () => {
    return operTypesList.map((operType) => (
      <tr> 
				<td>{operType.name}</td>
				<td>{operType.exec_time}</td>
				<td>
					<Button className="px-0" onClick={() => editItem(operType)}>
						<EditIcon/>
					</Button>
					<Button className="px-0" onClick={() => handleDelete(operType)} >
						<DeleteIcon/>
					</Button>
				</td>
    	</tr>
  	));
  }

	const toggle = () => {
    setModal(!modal);
  }

  return (
		<div className="text-center">
			<h3 className="text-success text-uppercase text-center my-4">
				Операции
			</h3>
			<div className="col-md-4 col-sm-60 mx-auto p-0">        
				<div className="">
					<button onClick={createItem} className="btn btn-info m-3">
						Добавить операцию
					</button>
				</div>
				{ 
					operTypesList.length > 0 ? 
					<Table className="mt-4" striped> 
						<thead> 
							<tr> 
								<th>Название</th> 
								<th>Время выполнения</th>
								<th></th>
							</tr> 
						</thead> 
						<tbody> 
							{renderItems()}
						</tbody> 
					</Table> 
					: <div className="mt-3">Нет операций</div>
				}
			</div>
			{ modal ? (
				<OperationTypesModal
					activeItem={activeItem}
					toggle={toggle}
					onSave={handleSubmit}
				/>
			) : null}
		</div>
	);
}

export default OperationTypesPage;

