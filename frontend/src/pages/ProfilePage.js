import React, { useContext, useEffect, useState } from 'react'
import {
  Label
} from "reactstrap";
import { useNavigate } from 'react-router-dom';

import AuthContext from "../context/AuthContext";
import profileService from "../servicies/ProfileService";

const RegisterPage = () => {
  let [ userData, setUserData ] = useState({});
  let { authTokens } = useContext(AuthContext);
  let navigate = useNavigate();

  useEffect(() => {
    if (!authTokens) navigate('/login');
    profileService.getProfileData(authTokens.access)
      .then(res => {
        setUserData({
            email: res.data.email,
            firstName: res.data.first_name,
            lastName: res.data.last_name
        });
      })
      .catch(err => {
        console.log(err);
      });
  }, [authTokens, setUserData, navigate])


  return (
    <div className="card card-container col-md-7 col-sm-60 mx-auto p-0 mt-5">
      <h3 className="text-success text-uppercase text-center mt-4">
        Профиль
      </h3>
      <div className='m-4'>
        <Label>Имя: { userData.firstName }</Label><hr/>
        <Label>Фамилия: { userData.lastName }</Label><hr/>
        <Label>Почтовый адрес: { userData.email }</Label>
      </div>
    </div>
  )
}

export default RegisterPage;

