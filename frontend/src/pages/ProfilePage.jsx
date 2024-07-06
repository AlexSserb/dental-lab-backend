import React, { useContext, useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box, Typography, Button, TextField, Alert,
  Stack, Paper
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DoneIcon from "@mui/icons-material/Done";

import AuthContext from "../context/AuthContext";
import profileService from "../servicies/ProfileService";
import ModalChangePassword from "../modals/ModalChangePassword";
import GridContainer from "../components/GridContainer";


const boxStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center"
};

const ProfilePage = () => {
  const [userData, setUserData] = useState({});
  const { authTokens, userGroupToString, user, logoutUser } = useContext(AuthContext);
  const navigate = useNavigate();
  const { state } = useLocation();
  const [message, setMessage] = useState("");
  const [messageSeverity, setMessageSeverity] = useState("error");
  const [isFirstNameEdit, setIsFirstNameEdit] = useState(false);
  const [isLastNameEdit, setIsLastNameEdit] = useState(false);

  const formatAndSetUserData = (data) => {
    setUserData({
      email: data.email,
      firstName: data.firstName,
      lastName: data.lastName,
      group: userGroupToString(data.group),
      createdAt: data.createdAt
    });
  };

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
    profileService.getProfileData(state?.email)
      .then(res => formatAndSetUserData(res.data))
      .catch(err => {
        console.log(err);
      });
  }, []);

  const saveFirstName = () => {
    if (isFirstNameEdit) {
      profileService.patchUserFirstName(user?.email, userData.firstName)
        .then(res => {
          formatAndSetUserData(res.data);
          setMessageSeverity("success");
          setMessage("Имя изменено.");
          setIsFirstNameEdit(false);
        })
        .catch(err => {
          setMessageSeverity("error");
          setMessage("Ошибка. Редактирование профиля не доступно.");
          console.log(err);
        });
    }
    else {
      setIsFirstNameEdit(true);
    }
  };

  const renderFirstName = () => {
    return (
      <Box sx={boxStyle}>
        {
          isFirstNameEdit ?
            <TextField name="firstName" label="Имя" variant="outlined"
              value={userData.firstName} onChange={e => setUserData({ ...userData, firstName: e.target.value })} />
            : <Typography>Имя: {userData.firstName}</Typography>
        }
        <Box sx={{ marginBottom: 1 }}>
          {
            user?.email === userData.email && (
              <Button variant="contained" onClick={saveFirstName}>
                {isFirstNameEdit ? <DoneIcon /> : <EditIcon />}
              </Button>
            )
          }
        </Box>
      </Box>
    );
  };

  const saveLastName = () => {
    if (isLastNameEdit) {
      profileService.patchUserLastName(user?.email, userData.lastName)
        .then(res => {
          formatAndSetUserData(res.data);
          setMessageSeverity("success");
          setMessage("Фамилия изменена.");
          setIsLastNameEdit(false);
        })
        .catch(err => {
          setMessageSeverity("error");
          setMessage("Ошибка. Редактирование профиля не доступно.");
          console.log(err);
        });
    }
    else {
      setIsLastNameEdit(true);
    }
  };

  const renderLastName = () => {
    return (
      <Box sx={boxStyle}>
        {
          isLastNameEdit ?
            <TextField name="lastName" label="Фамилия" variant="outlined"
              value={userData.lastName} onChange={e => setUserData({ ...userData, lastName: e.target.value })} />
            : <Typography>Фамилия: {userData.lastName}</Typography>
        }
        <Box sx={{ marginBottom: 1 }}>
          {
            user?.email === userData.email && (
              <Button variant="contained" onClick={saveLastName}>
                {isLastNameEdit ? <DoneIcon /> : <EditIcon />}
              </Button>
            )
          }
        </Box>
      </Box>
    );
  };

  const handleClickLogoutUser = () => {
    logoutUser();
    navigate('/login');
  };

  return (
    <GridContainer>
      <Stack sx={{
        display: "flex",
        width: "33%",
        minWidth: "400px",
        spacing: 3
      }}>
        <Paper elevation={5} sx={{ padding: 5, marginTop: 3 }}>
          <Typography textAlign={"center"} variant="h5" component="h5" sx={{ paddingBlockEnd: 3 }}>
            Профиль
          </Typography>
          {message && <Alert sx={{ marginBottom: 2 }} severity={messageSeverity}>{message}</Alert>}

          {renderLastName()}<hr />

          {renderFirstName()}<hr />

          <p>Почтовый адрес: {userData.email}</p><hr />

          <p>Должность: {userData.group}</p><hr />

          <p>Дата регистрации: {userData.createdAt}</p><hr />

          {
            user?.email === userData.email ? (
              <>
                <ModalChangePassword
                  setProfileMessage={setMessage}
                  setProfileMessageSeverity={setMessageSeverity}
                />
                <Button variant="contained" onClick={() => handleClickLogoutUser()}>
                  Выйти
                </Button>
              </>
            ) : (
              <Button variant="contained" onClick={() => navigate("/schedule", { state: { techEmail: userData.email } })}>
                Расписание
              </Button>
            )
          }
        </Paper>
      </Stack>
    </GridContainer>
  );
};

export default ProfilePage;
