import React, { useContext, useEffect } from 'react'
import { Link } from 'react-router-dom';
import {
  Button, TextField, Typography, FormControl,
  Grid, Stack, Paper, Alert
} from "@mui/material";

import AuthContext from '../context/AuthContext';


const RegisterPage = () => {
  let { registerUser, message, setMessage } = useContext(AuthContext);

  useEffect(() => {
    setMessage("");
  }, [setMessage])

  const handleRegister = (e) => {
    e.preventDefault();

    setMessage("");

    if (e.target.password.value !== e.target.passwordRepeat.value) {
      setMessage("Пароли не совпадают.");
    }
    else if (e.target.password.value.length < 8) {
      setMessage("Пароль должен состоять не менее чем из 8-ми символов.");
    }
    else {
      registerUser(e);
    }
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
        width: "40%",
        minWidth: "500px",
        spacing: 3
      }}>
        <Paper elevation={5} sx={{ padding: 3, marginTop: 3 }}>
          <Typography textAlign={"center"} variant="h5" component="h5" sx={{ paddingBlockEnd: 3 }}>
            Регистрация
          </Typography>
          <div className='m-4'>
            <form onSubmit={handleRegister}>
              <FormControl sx={{ paddingBlockEnd: 3 }}>
                <TextField
                  label="Почта"
                  type="email"
                  name="email"
                  required
                  inputProps={{ maxLength: 64 }}
                />
              </FormControl><br />
              <FormControl sx={{ paddingBlockEnd: 3, paddingRight: 3 }}>
                <TextField
                  label="Имя"
                  type="text"
                  name="firstName"
                  required
                  inputProps={{ maxLength: 64 }}
                />
              </FormControl>
              <FormControl sx={{ paddingBlockEnd: 3 }}>
                <TextField
                  label="Фамилия"
                  type="text"
                  name="lastName"
                  required
                  inputProps={{ maxLength: 64 }}
                />
              </FormControl><br />
              <FormControl sx={{ paddingBlockEnd: 3, paddingRight: 3 }}>
                <TextField
                  label="Пароль"
                  type="password"
                  name="password"
                  required
                  inputProps={{ maxLength: 20 }}
                />
              </FormControl>
              <FormControl sx={{ paddingBlockEnd: 3 }}>
                <TextField
                  label="Повтор пароля"
                  type="password"
                  name="passwordRepeat"
                  required
                  inputProps={{ maxLength: 20 }}
                />
              </FormControl><br />
              {message && (
                <Alert severity="error">
                  {message}
                </Alert>
              )}
              <p><Link to="/login">Уже есть аккаунт</Link></p>
              <Button variant="contained" type="submit" sx={{ padding: 2 }}>
                Зарегистрироваться
              </Button>
            </form>
          </div>
        </Paper>
      </Stack>
    </Grid>
  )
}

export default RegisterPage;

