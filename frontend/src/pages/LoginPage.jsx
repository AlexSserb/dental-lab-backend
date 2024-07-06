import React, { useContext, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Button, TextField, Typography, FormControl,
  Stack, Paper
} from "@mui/material";

import AuthContext from '../context/AuthContext';
import GridContainer from '../components/GridContainer';

const LoginPage = () => {
  const { loginUser, message, setMessage } = useContext(AuthContext);

  useEffect(() => {
    setMessage("");
  }, [setMessage]);

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
            </FormControl><br />
            <FormControl sx={{ paddingBlockEnd: 3 }}>
              <TextField
                label="Пароль"
                type="password"
                name="password"
                required
              />
            </FormControl><br />
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
    </GridContainer>
  );
};

export default LoginPage;

