import React, { useContext, useEffect } from 'react'
import { Link } from 'react-router-dom';
import {
  Button, Form, FormGroup, Input, Label
} from "reactstrap";

import AuthContext from '../context/AuthContext';


const LoginPage = () => {
  let { loginUser, message, setMessage } = useContext(AuthContext);

  useEffect(() => {
    setMessage("");
  }, [setMessage])

  return (
    <div className="card card-container col-md-4 col-sm-60 mx-auto p-0 mt-5">
      <h3 className="text-success text-uppercase text-center mt-4">
        Вход
      </h3>
      <div className='m-4'>
        <Form onSubmit={loginUser}>
          <FormGroup>
            <Label for="email">Почта</Label>
            <Input
              type="email"
              name="email"
              required
            />
          </FormGroup>
          <FormGroup>
            <Label for="password">Пароль</Label>
            <Input
              type="password"
              name="password"
              required
            />
          </FormGroup>
          { message && (
            <div className="form-group">
              <div className="alert alert-danger" role="alert">
                {message}
              </div>
            </div>
          )}
          <p><Link to="/registration">Зарегистрироваться</Link></p>
          <Button type="submit" color="success">
            Войти
          </Button>
        </Form>
      </div>
    </div>
  )
}

export default LoginPage;

