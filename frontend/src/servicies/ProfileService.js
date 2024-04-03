import axios from "axios";

const API_URL = "accounts/";


class ProfileService {
  getProfileData(email) {
    return axios.get(API_URL + `profile/${email}`);
  }

  patchUserFirstName(email, firstName) {
    return axios.patch(API_URL + `profile/edit-first-name/${email}/${firstName}`);
  }

  patchUserLastName(email, lastName) {
    return axios.patch(API_URL + `profile/edit-last-name/${email}/${lastName}`);
  }

  postPasswordChange(oldPassword, newPassword) {
    return axios.post(API_URL + `password-change/`, { 
      "oldPassword": oldPassword, 
      "newPassword": newPassword
    });
  }
}

const profileService = new ProfileService();
export default profileService;
