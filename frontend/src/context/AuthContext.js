import { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export default AuthContext;


export const AuthProvider = ({children}) => {
	let [authTokens, setAuthTokens] = useState(() => localStorage.getItem('authTokens') ? 
		JSON.parse(localStorage.getItem('authTokens')) : null);
	let [user, setUser] = useState(() => localStorage.getItem('authTokens') ? 
		jwtDecode(localStorage.getItem('authTokens')) : null);

	let [loading, setLoading] = useState(true);
	let [message, setMessage] = useState("");

	let navigate = useNavigate();

	let loginUser = (e) => {
		e.preventDefault();
		setMessage("");
		axios.post('/accounts/token/',
			{ 
				'email': e.target.email.value, 
				'password': e.target.password.value 
			})
			.then(res => {
				setAuthTokens(res.data);
				setUser(jwtDecode(res.data.access));
				localStorage.setItem('authTokens', JSON.stringify(res.data));
				navigate('/');
			})
			.catch(err => {
				console.log(err);
				if (err.response?.status === 401) {
					setMessage("Неверный почтовый адрес или пароль.");
				}
				else {
					defaultAuthErrorHandling(err, "Ошибка входа в систему.");
				}
			});
	}

	let registerUser = (e) => {
		e.preventDefault();
		axios.post('/accounts/register/',
			{
				'first_name': e.target.firstName.value,
				'last_name': e.target.lastName.value,
				'email': e.target.email.value,
				'password': e.target.password.value 
			})
			.then(res => {
				setAuthTokens(res.data);
				setUser(jwtDecode(res.data.access));
				localStorage.setItem('authTokens', JSON.stringify(res.data));
				navigate('/');
			})
			.catch(err => {
				if (err.response?.data?.email[0] === "user with this email already exists.") {
					setMessage("Ошибка. Пользователь с данным почтовым адресом уже зарегистрирован.");
				}
				else if (err.response?.data?.email[0] === "Enter a valid email address.") {
					setMessage("Ошибка. Введите корректный почтовый адрес.");
				}
				else {
					defaultAuthErrorHandling(err, "Ошибка регистрации.");
				}
			});
	}

	let defaultAuthErrorHandling = (err, defaultErrorMsg) => {
		if (!err.response) {
			setMessage("Ошибка. Не удалось подключиться к серверу.");
		}
		else {
			console.log(err);
			setMessage(defaultErrorMsg);
		}
	}

	let logoutUser = () => {
		setAuthTokens(null);
		setUser(null);
		localStorage.removeItem('authTokens');
	}

	let updateToken = () => {
		console.log('Update token call!');
		axios.post('/accounts/token/refresh/',
			{ 'refresh': authTokens?.refresh })
			.then((res) => {
				setAuthTokens(res.data);
				setUser(jwtDecode(res.data.access));
				localStorage.setItem('authTokens', JSON.stringify(res.data));
			})
			.catch(_ => logoutUser())
			.finally(() => setLoading(false));
	}

	let userGroupToString = (group) => {
		if (!group) {
			return "Врач";
		}
		return group;
	}

	let contextData = {
		user: user,
		authTokens: authTokens,
		userGroupToString: userGroupToString,
		loginUser: loginUser,
		registerUser: registerUser,
		message: message,
		setMessage: setMessage,
		logoutUser: logoutUser
	}

	useEffect(() => {
		if (loading) {
			updateToken();
		}

		let minutes = 1000 * 60 * 9.5;
		let interval = setInterval(() => {
			if (authTokens) {
				updateToken();
			}
		}, minutes);
		return () => clearInterval(interval);
	}, [authTokens, loading])

  return (
    <AuthContext.Provider value={contextData}>
      {loading ? null : children}
    </AuthContext.Provider>
  )
}
