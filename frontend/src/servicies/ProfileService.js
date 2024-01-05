import axios from 'axios';

const API_URL = "api/";


class ProfileService {
  getProfileData(accessToken) {
    return axios.get(API_URL + 'profile/', {
      headers: {
        'Authorization': 'Bearer ' + String(accessToken)
      }
    });
  }
}

const profileService = new ProfileService();
export default profileService;
