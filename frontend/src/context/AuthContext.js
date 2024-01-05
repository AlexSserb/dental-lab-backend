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
		axios.post('/api/token/',
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
					setMessage("Неверное имя или пароль.");
				}
				else {
					setMessage("Ошибка. Не удалось подключиться к серверу.");
				}
			});
	}

	let registerUser = (e) => {
		e.preventDefault();
		axios.post('/api/register/',
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
				setMessage("Ошибка регистрации.");
			});
	}

	let logoutUser = () => {
		setAuthTokens(null);
		setUser(null);
		localStorage.removeItem('authTokens');
	}

	let updateToken = () => {
		console.log('Update token call!');
		axios.post('/api/token/refresh/',
			{ 'refresh': authTokens?.refresh })
			.then((res) => {
				setAuthTokens(res.data);
				setUser(jwtDecode(res.data.access));
				localStorage.setItem('authTokens', JSON.stringify(res.data));
			})
			.catch(_ => logoutUser())
			.finally(() => setLoading(false));
	}

	let contextData = {
		user: user,
		authTokens: authTokens,
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

		let fourMinutes = 1000 * 60 * 4;
		let interval = setInterval(() => {
			if (authTokens) {
				updateToken();
			}
		}, fourMinutes);
		return () => clearInterval(interval);
	}, [authTokens, loading])

  return (
    <AuthContext.Provider value={contextData}>
      {loading ? null : children}
    </AuthContext.Provider>
  )
}
