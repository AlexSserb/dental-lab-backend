import axios from 'axios';

const API_URL = "accounts/";


class ProfileService {
  getProfileData(email) {
    return axios.get(API_URL + `profile/${email}`);
  }
}

const profileService = new ProfileService();
export default profileService;
