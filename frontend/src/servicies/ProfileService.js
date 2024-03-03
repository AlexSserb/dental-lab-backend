import axios from 'axios';

const API_URL = "accounts/";


class ProfileService {
  getProfileData() {
    return axios.get(API_URL + 'profile/');
  }
}

const profileService = new ProfileService();
export default profileService;
