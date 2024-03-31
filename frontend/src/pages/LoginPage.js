import React, { useContext, useEffect } from 'react'
import { Link } from 'react-router-dom';
import {
  Button, TextField, Typography, FormControl,
  Grid, Stack, Paper
} from "@mui/material";

import AuthContext from '../context/AuthContext';


const LoginPage = () => {
  let { loginUser, message, setMessage } = useContext(AuthContext);

  useEffect(() => {
    setMessage("");
  }, [setMessage])

  return (
    <Grid container sx={{
      spacing: 0,
      direction: "column",
      alignItems: "center",
      justifyContent: "center"
    }}>
      <Stack sx={{
        display: "flex",
        width: "40%",
        minWidth: "500px",
        spacing: 3
      }}>
        <Paper elevation={5} sx={{ padding: 3, marginTop: 3 }}>
          <Typography textAlign={"center"} variant="h5" component="h5" sx={{ paddingBlockEnd: 3 }}>
            Вход
          </Typography>
          <form onSubmit={loginUser}>
            <FormControl sx={{ paddingBlockEnd: 3 }}>
              <TextField
                label="Почта"
                type="email"
                name="email"
                required
              />
            </FormControl><br/>
            <FormControl sx={{ paddingBlockEnd: 3 }}>
              <TextField
                label="Пароль"
                type="password"
                name="password"
                required
              />
            </FormControl><br/>
            {message && (
              <div className="form-group">
                <div className="alert alert-danger" role="alert">
                  {message}
                </div>
              </div>
            )}
            <p><Link to="/registration">Зарегистрироваться</Link></p>
            <Button variant="contained" type="submit" sx={{ padding: 2 }}>
              Войти
            </Button>
          </form>
        </Paper>
      </Stack>
    </Grid>
  )
}

export default LoginPage;

