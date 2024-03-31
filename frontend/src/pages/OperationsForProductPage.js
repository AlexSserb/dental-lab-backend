import React, { useEffect, useState, useContext } from "react";
import {
	Typography,
	Box, Stack, Grid,
	Accordion, AccordionSummary, AccordionDetails, Paper,
	Table, TableBody, TableRow, TableHead, TableCell
} from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { useNavigate, useLocation, Link } from "react-router-dom";
import moment from "moment";

import ToothMarks from "../components/ToothMarks";
import operationService from "../servicies/OperationService";
import AuthContext from '../context/AuthContext';
import getDepartmentName from "../utils/GetDepartmentName";


const OperationsForProductPage = () => {
	const { authTokens } = useContext(AuthContext);
	const [operations, setOperations] = useState([]);
	const [operationStatuses, setOperationStatuses] = useState([]);
	const { state } = useLocation();
	const { product } = state;

	const navigate = useNavigate();

	const getOperations = () => {
		operationService.getForProduct(product.id)
			.then(res => {
				setOperations(res.data);
			})
			.catch(err => console.log(err));
	}

	useEffect(() => {
		if (!authTokens || !authTokens.access) {
			navigate('/login');
			return;
		}

		getOperations();

		operationService.getOperationStatuses()
			.then(res => {
				const operations = res.data.map(oper => { return { key: oper.id, value: oper.name } });
				setOperationStatuses(operations);
			})
			.catch(err => console.log(err));
	}, [])

	const operationHistory = (history) => {
		return history.map((entity) => (
			<TableRow>
				<TableCell>
					{moment(entity.pgh_created_at).format("YYYY.MM.DD HH:mm:ss")}
				</TableCell>
				<TableCell>
					{entity.operation_status.name}
				</TableCell>
			</TableRow>
		));
	}

	const renderOperations = () => {
		return operations.map((oper) => (
			<Accordion>
				<AccordionSummary
					expandIcon={<ExpandMoreIcon />}
					aria-controls="panel1-content"
					id="panel1-header"
				>
					<Stack>
						<Typography item>Вид операции: {oper.operation_type.name}</Typography>
						<Typography item>{getDepartmentName(oper.operation_type.group)}</Typography>
						<Typography item>Статус операции: {oper.operation_status.name}</Typography>
						<Typography item>
							Время выполнения: {oper.operation_type.exec_time.substring(0, 2)}:
							{oper.operation_type.exec_time.substring(3, 5)}
						</Typography>
						<Typography>
							<>Назначена технику: </> 
							<Link to="/profile" state={{ email: oper.tech.email }}>
								{oper.tech.last_name} {oper.tech.first_name}
							</Link>
						</Typography>
					</Stack>
				</AccordionSummary>
				<AccordionDetails>
					<Grid container spacing={2} justifyContent={"space-between"}>
						<Grid item>
							История изменений статусов:
							<Table>
								<TableHead>
									<TableRow>
										<TableCell>Дата и время</TableCell>
										<TableCell>Статус</TableCell>
									</TableRow>
								</TableHead>
								<TableBody>
									{operationHistory(oper.history)}
								</TableBody>
							</Table>
						</Grid>
					</Grid>
				</AccordionDetails>
			</Accordion>
		));
	}

	return (
		<Grid container sx={{
			spacing: 0,
			direction: "column",
			alignItems: "center",
			justifyContent: "center"
		}}>
			<Stack container sx={{
				display: "flex",
				width: "70%",
				minWidth: "500px",
				spacing: 3
			}}>
				<Box sx={{
					border: 1,
					borderRadius: 2,
					borderColor: '#4d4c4c',
					padding: 3,
					marginTop: 5,
					alignItems: "center"
				}}>
					<Typography textAlign={"center"} variant="h4" component="h5" sx={{ paddingBottom: 4 }}>
						Информация об изделии
					</Typography>
					<Paper sx={{ marginBottom: 2, padding: 2 }}>
						<Typography>Тип изделия: {product.product_type.name}</Typography>
						<Typography>Количество: {product.amount}</Typography>
						<Typography>Статус: {product.product_status.name}</Typography>
						<Typography>Формула:</Typography>
						<Paper sx={{ marginY: 1, padding: 2 }}>
							<ToothMarks teethList={product.teeth} />
						</Paper>
					</Paper>
					{
						operations?.length > 0 ?
							<>
								<Typography textAlign={"center"} variant="h5" component="h5" sx={{ paddingY: 2 }}>
									Операции для изделия
								</Typography>
								{renderOperations()}
							</>
							:
							<Typography textAlign={"center"}>
								Для изделия нет операций, так как не оформлен наряд.
							</Typography>
					}
				</Box>
			</Stack>
		</Grid>
	);
}
export default OperationsForProductPage;
