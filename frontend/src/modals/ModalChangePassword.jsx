import React, { useState } from "react";
import {
    Button, Typography, Modal,
    Stack, Box, TextField, Alert
} from "@mui/material";

import profileService from "../servicies/ProfileService";
import { modalStyle } from "./styles/ModalChangePasswordStyle";
import { modalTitleStyle } from "./styles/ModalStyle";


export const ModalChangePassword = ({ setProfileMessage, setProfileMessageSeverity }) => {
    const [open, setOpen] = useState(false);
    const handleOpen = () => setOpen(true);
    const handleClose = () => setOpen(false);

    const [oldPassword, setOldPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [repeatNewPassword, setRepeatNewPassword] = useState("");
    const [message, setMessage] = useState("");

    const handleSubmit = () => {
        setMessage("");
        if (newPassword !== repeatNewPassword) {
            setMessage("Пароли не совпадают.");
            return;
        }

        if (newPassword.length < 8) {
            setMessage("Пароль должен состоять не менее чем из 8-ми символов.");
            return;
        }

        profileService.postPasswordChange(oldPassword, newPassword)
            .then(_ => {
                setProfileMessageSeverity("success");
                setProfileMessage("Пароль успешно изменен.");
                handleClose();
            })
            .catch(err => {
                if (err?.response?.data?.old_password[0] === "Wrong password") {
                    setMessage("Неправильный старый пароль.");
                }
                else {
                    setMessage("Ошибка смены пароля.");
                }
            });
    };

    return (
        <div>
            <Button variant="contained" sx={{ marginBottom: 2 }} onClick={handleOpen}>
                Изменить пароль
            </Button>
            <Modal
                open={open}
                onClose={handleClose}
            >
                <Box sx={modalStyle}>
                    <Typography variant="h5" component="h5" sx={modalTitleStyle}>
                        Изменение пароля
                    </Typography>

                    <Stack spacing={1}>
                        <TextField
                            type="password"
                            label="Старый пароль"
                            initialValue={oldPassword}
                            onChange={event => setOldPassword(event.target.value)} />
                        <TextField
                            type="password"
                            label="Новый пароль"
                            initialValue={newPassword}
                            onChange={event => setNewPassword(event.target.value)}
                            inputProps={{ maxLength: 20 }} />
                        <TextField
                            type="password"
                            label="Повтор пароля"
                            initialValue={repeatNewPassword}
                            onChange={event => setRepeatNewPassword(event.target.value)}
                            inputProps={{ maxLength: 20 }} />
                        {message && <Alert sx={{ marginBottom: 2 }} severity="error">{message}</Alert>}
                        <Button variant="contained" onClick={handleSubmit}>
                            Изменить
                        </Button>
                    </Stack>
                </Box>
            </Modal>
        </div>
    );
};

export default ModalChangePassword;
