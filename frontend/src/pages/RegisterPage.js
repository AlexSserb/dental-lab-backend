import React, { useContext, useEffect } from 'react'
import { Link } from 'react-router-dom';
import {
  Button, Form, FormGroup, Input, Label
} from "reactstrap";

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
    else {
      registerUser(e);
    }
  }

  return (
    <div className="card card-container col-md-4 col-sm-60 mx-auto p-0 mt-5">
      <h3 className="text-success text-uppercase text-center mt-4">
        Регистрация
      </h3>
      <div className='m-4'>
        <Form onSubmit={handleRegister}>
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
          <FormGroup>
            <Label for="passwordRepeat">Повтор пароля</Label>
            <Input
              type="password"
              name="passwordRepeat"
              required
            />
          </FormGroup>
          {message && (
            <div className="form-group">
              <div className="alert alert-danger" role="alert">
                {message}
              </div>
            </div>
          )}
          <p><Link to="/login">Уже есть аккаунт</Link></p>
          <Button type="submit" color="success">
            Зарегистрироваться
          </Button>
        </Form>
      </div>
    </div>
  )
}

export default RegisterPage;

