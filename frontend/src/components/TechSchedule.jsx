import { useEffect, useRef, useContext } from "react";
import { Stack, Typography, Box } from "@mui/material";
import FullCalendar from "@fullcalendar/react";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from '@fullcalendar/interaction';
import ruLocale from "@fullcalendar/core/locales/ru";

import { useNavigate, useLocation } from "react-router-dom";

import AuthContext from '../context/AuthContext';
import operationService from "../servicies/OperationService";
import { isPhysician, isDirector, isChiefTech, isLabAdmin } from "../utils/Permissions";

const TechSchedule = () => {
    const { authTokens, user } = useContext(AuthContext);
    const { state } = useLocation();
    const techEmail = state?.techEmail || user.email;
    let isEditable = isDirector(user) || isLabAdmin(user) || isChiefTech(user);
    const calendarRef = useRef();
    let operations = [];
    const navigate = useNavigate();

    useEffect(() => {
        if (!authTokens || !authTokens.access) {
            navigate("/login");
            return;
        }

        if (isPhysician(user)) {
            navigate("/");
            return;
        }
    }, []);

    const renderEventContent = (eventInfo) => {
        const operInfo = eventInfo.event.extendedProps;
        return (
            <div style={{ margin: 3 }}>
                <b>{eventInfo.timeText}</b><br />
                <span>{operInfo.operationType?.name}</span>
            </div>
        );
    };

    const formatDate = (date) => `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;

    const handleEventDrop = (event) => {
        operationService.setOperationExecStart(event.event.id, event.event.start.toUTCString())
            .then(_ => {
                const calendar = calendarRef?.current?.getApi();
                operations = calendar.getEvents();
            })
            .catch(err => console.log(err));
    };

    async function getCalendarData(fetchInfo, successCallback) {
        await operationService.getForSchedule(techEmail, formatDate(fetchInfo.start))
            .then(res => {
                if (res?.data?.length === 0) operations = [];
                else operations = res.data;
                successCallback(res.data);
            })
            .catch(err => console.log(err));
    }

    return (
        <Stack>
            <Typography textAlign={"center"} variant="h4" component="h5" sx={{ paddingTop: 2 }}>
                Расписание {techEmail}
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
                    timeZone="local"

                    ref={calendarRef}
                    events={
                        (fetchInfo, successCallback) => getCalendarData(fetchInfo, successCallback)
                    }
                    eventContent={renderEventContent}
                    eventDrop={handleEventDrop}

                    slotMinTime={'8:00'}
                    slotMaxTime={'19:00'}
                    snapDuration={'00:01'}
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
    );
};

export default TechSchedule;
