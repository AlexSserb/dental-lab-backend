import { useEffect, useRef, useContext, useState } from "react";
import { Stack, Typography, Box, Grid, Paper, Button, Alert, Select, MenuItem } from "@mui/material";
import Edit from "@mui/icons-material/Edit";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import ruLocale from "@fullcalendar/core/locales/ru";

import { useNavigate, useLocation } from "react-router-dom";

import { DateTimePicker, LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import "dayjs/locale/ru";
import dayjs from "dayjs";
import utc from 'dayjs/plugin/utc';
import timezone from 'dayjs/plugin/timezone';

import AuthContext from "../context/AuthContext";
import operationService from "../servicies/OperationService";
import { isPhysician } from "../utils/Permissions";
import { getDepartmentName, getDepartmentIdByCode } from "../utils/GetDepartmentInfo";
import productService from "../servicies/ProductService";
import profileService from "../servicies/ProfileService";


const AssignOperationsPage = () => {
    const { authTokens, user } = useContext(AuthContext);
    const { state } = useLocation();
    let [operationsToAssign, setOperationsToAssign] = useState([]);
    const [currOperation, setCurrOperation] = useState();
    const [execStart, setExecStart] = useState();
    const [techEmail, setTechEmail] = useState("1");

    const calendarRef = useRef();
    const [message, setMessage] = useState("");
    const [techs, setTechs] = useState([]);
    let operations = [];

    const navigate = useNavigate();

    const getProductsWithOperations = () => {
        operationsToAssign = [];
        productService.getWithOperationsForOrder(state.order.id)
            .then(res => {
                let operations = [];
                res.data.forEach(product => operations.push(...product.operations));
                setOperationsToAssign(operations);
            })
            .catch(err => {
                console.log(err);
            });
    }

    useEffect(() => {
        if (!authTokens || !authTokens.access) {
            navigate("/login");
            return;
        }

        if (isPhysician(user)) {
            navigate("/");
            return;
        }

        dayjs.extend(utc);
        dayjs.extend(timezone);

        getProductsWithOperations();
    }, []);

    const renderEventContent = (eventInfo) => {
        const operInfo = eventInfo.event.extendedProps;

        return (
            <Box sx={{ margin: 1 }}>
                <b>{eventInfo.timeText}</b><br />
                <span>{operInfo.operationType?.name}</span>
            </Box>
        )
    }

    const formatDate = (date) => `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;

    const handleEventDrop = (event) => {
        operationService.setOperationExecStart(event.event.id, event.event.start.toUTCString())
            .then(_ => {
                const calendar = calendarRef?.current?.getApi();
                operations = calendar.getEvents();
            })
            .catch(err => console.log(err));
    }

    async function getCalendarData(fetchInfo, successCallback) {
        if (techEmail) {
            await operationService.getForSchedule(techEmail, formatDate(fetchInfo.start))
                .then(res => {
                    if (res?.data?.length === 0) operations = [];
                    else operations = res.data;
                    successCallback(res.data);
                })
                .catch(err => console.log(err));
        } else {
            successCallback([]);
            operations = [];
        }
    }

    const selectOperation = (operation) => {
        setCurrOperation(operation);
        setTechEmail(operation.tech?.email ? operation.tech.email : "1");
        setExecStart(operation.execStart);
        profileService.getTechnicians(getDepartmentIdByCode(operation.operationType.group))
            .then(res => {
                setTechs(res.data);
            })
            .catch(err => console.log(err));
    }

    const saveOperation = () => {
        setMessage("");

        if (!execStart) {
            setMessage("Дата и время не выбраны");
            return;
        }
        if (!techEmail) {
            setMessage("Техник не выбран");
            return;
        }

        currOperation.tech = techs.find(tech => tech.email === techEmail);
        currOperation.execStart = execStart;
        operationService.assignOperation(currOperation)
            .then(_ => getProductsWithOperations())
            .catch(err => console.log(err));
    }

    const selectTech = (event) => {
        setTechEmail(event.target.value);
    }

    const formatExecTime = (time) => {
        return `${Number(time.substring(0, 2))} ч. ${Number(time.substring(3, 5))} мин.`;
    }

    const renderOpeartions = () => {
        return operationsToAssign.map(operation => (
            <Grid sx={{
                padding: 2,
                marginY: 1,
                border: 2,
                borderRadius: "8px",
                backgroundColor: operation.id === currOperation?.id ? "#dcf0fa" : "#FFFFFF"
            }}>
                <Box>
                    <Typography>Тип операции: {operation.operationType.name}</Typography>
                    <Typography>Группа: {getDepartmentName(operation.operationType.group)}</Typography>
                    <Typography>Время выполнения: {formatExecTime(operation.operationType.execTime)}</Typography>
                    {
                        operation.tech ? (
                            <>
                                <Typography>Назначена технику: {operation.tech.lastName} {operation.tech.firstName}</Typography>
                                <Typography>На дату и время: {dayjs(operation.execStart).format("YYYY.MM.DD HH:mm")}</Typography>
                            </>
                        )
                            : <Typography>Техник не назначен</Typography>
                    }
                </Box>
                <Box margin="2">
                    <Button variant="contained" onClick={() => selectOperation(operation)}>
                        <Edit />
                    </Button>
                </Box>
            </Grid>
        ))
    }

    return (
        <Stack>
            <Typography textAlign={"center"} variant="h5" component="h6" sx={{ paddingTop: 2 }}>
                Назначение операций техникам
            </Typography>
            <hr />
            <Grid container sx={{ padding: 2, direction: "row" }}>
                <Box sx={{ width: "30%", paddingRight: 2 }}>
                    <Stack component={Paper} sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography textAlign="center">
                            Назначение операции
                        </Typography><hr />
                        {
                            currOperation ?
                                <>
                                    <Typography>Тип операции: {currOperation?.operationType?.name}</Typography>
                                    <Typography>Группа: {getDepartmentName(currOperation?.operationType?.group)}</Typography>
                                    <Typography>Время выполнения: {formatExecTime(currOperation?.operationType?.execTime)}</Typography>
                                    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale={"ru"}>
                                        <DateTimePicker sx={{ marginY: 2 }}
                                            value={dayjs(execStart)} label="Начало выполнения"
                                            onChange={(value) => setExecStart(value)}
                                            minDate={dayjs(new Date("01-01-2010"))}
                                            maxDate={dayjs(new Date("01-01-2100"))} />
                                    </LocalizationProvider>
                                    <Select
                                        sx={{ marginBottom: 2 }}
                                        onChange={selectTech}
                                        value={techEmail}
                                    >
                                        {techs.map(tech => (
                                            <MenuItem value={tech.email}>{tech.lastName} {tech.firstName}</MenuItem>
                                        ))}
                                    </Select>
                                    {message && (
                                        <Alert severity="error">
                                            {message}
                                        </Alert>
                                    )}
                                    <Button margintop="1" variant="contained" onClick={() => saveOperation()}>
                                        Сохранить
                                    </Button>
                                </>
                                : <Typography>Операция не выбрана</Typography>
                        }

                    </Stack>
                    <Stack component={Paper} sx={{ padding: 2 }}>
                        <Typography textAlign="center">
                            Операции для заказа
                        </Typography><hr />
                        {
                            operationsToAssign?.length > 0 ? renderOpeartions()
                                : <Typography textAlign="center">Операций нет</Typography>
                        }
                    </Stack>
                </Box>

                <Box component={Paper} sx={{ width: "70%", padding: 2 }}>
                    <FullCalendar
                        plugins={[timeGridPlugin, interactionPlugin]}

                        locale={ruLocale}
                        editable={false}
                        eventDurationEditable={false}
                        selectable={true}
                        initialView="timeGridWeek"
                        weekends={false}
                        timeZone="local"

                        ref={calendarRef}
                        events={
                            (fetchInfo, successCallback) => getCalendarData(fetchInfo, successCallback)
                        }
                        eventContent={renderEventContent}
                        eventDrop={handleEventDrop}

                        slotMinTime={"8:00"}
                        slotMaxTime={"19:00"}
                        snapDuration={"00:01"}
                        slotDuration={"00:15"}

                        headerToolbar={{
                            left: "prev,next",
                            center: "title",
                            right: "timeGridWeek,timeGridDay"
                        }}
                    >
                    </FullCalendar>
                </Box>
            </Grid>
        </Stack>
    )
}

export default AssignOperationsPage;
