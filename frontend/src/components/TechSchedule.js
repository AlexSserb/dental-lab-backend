import { useEffect, useRef, useContext } from "react";
import { Stack, Typography, Box } from "@mui/material";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from '@fullcalendar/interaction';
import ruLocale from "@fullcalendar/core/locales/ru";

import { useNavigate } from "react-router-dom";

import AuthContext from '../context/AuthContext';
import operationService from "../servicies/OperationService";

const TechSchedule = () => {
    const { authTokens, userGroupToString, user } = useContext(AuthContext);
    const userGroup = userGroupToString(user?.group);
    let isEditable = userGroup.match(/^(А|Д|Г)/);
    const calendarRef = useRef();
    let operations = [];
    const navigate = useNavigate();

    useEffect(() => {
        if (!authTokens || !authTokens.access) {
            navigate("/login");
            return;
        }

        if (userGroup?.match(/^В/)) {
            navigate("/");
            return;
        }
    })

    const renderEventContent = (eventInfo) => {
        const operInfo = eventInfo.event.extendedProps;
        return (
            <div style={{ margin: 3 }}>
                <b>{eventInfo.timeText}</b><br />
                <span>{operInfo.operation_type?.name}</span>
            </div>
        )
    }

    const handleEventDrop = (_) => {
        const calendar = calendarRef?.current?.getApi();
        operations = calendar.getEvents();
    }

    async function getCalendarData(fetchInfo, successCallback) {
        const dateStart = fetchInfo.start;
        const formattedDate = `${dateStart.getFullYear()}-${dateStart.getMonth() + 1}-${dateStart.getDate()}`;

        await operationService.getForSchedule(user.email, formattedDate)
            .then(res => {
                console.log(res.data);
                operations = res.data;
                successCallback(res.data);
            })
            .catch(err => console.log(err));
    }

    return (
        <Stack>
            <Typography textAlign={"center"} variant="h4" component="h5" sx={{ paddingTop: 2 }}>
                Расписание
            </Typography>
            <hr />
            <Box sx={{ padding: 2, height: "100vh" }}>
                <FullCalendar
                    plugins={[timeGridPlugin, interactionPlugin]}

                    locale={ruLocale}
                    editable={isEditable}
                    eventDurationEditable={false}
                    selectable={true}
                    initialView="timeGridWeek"
                    weekends={false}

                    ref={calendarRef}
                    events={
                        (fetchInfo, successCallback) => getCalendarData(fetchInfo, successCallback)
                    }
                    eventContent={renderEventContent}
                    eventDrop={handleEventDrop}

                    slotMinTime={'8:00'}
                    slotMaxTime={'19:00'}
                    snapDuration={'00:05'}
                    slotDuration={'00:15'}

                    headerToolbar={{
                        left: "prev,next",
                        center: "title",
                        right: "timeGridWeek,timeGridDay"
                    }}
                >
                </FullCalendar>
            </Box>
        </Stack>
    )
}

export default TechSchedule;
