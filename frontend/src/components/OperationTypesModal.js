import React, { useState } from "react";
 
import {
  Button,
  Modal,
  ModalHeader,
  ModalBody,
  Form,
  FormGroup,
  Input,
  Label
} from "reactstrap";


const OperationTypesModal = (props) => {
  let [activeItem, setActiveItem] = useState(props.activeItem);

  const handleChange = (e) => {
    setActiveItem({ ...activeItem, [e.target.name]: e.target.value});
  }

  return (
    <Modal isOpen={true} toggle={props.toggle}>
      <ModalHeader toggle={props.toggle}> Операция </ModalHeader>
      <ModalBody>
        <Form onSubmit={() => { props.onSave(activeItem); }}>
          <FormGroup>
            <Label for="name">Название</Label>
            <Input
              required
              type="text"
              name="name"
              value={activeItem.name}
              onChange={handleChange}
            />
          </FormGroup>

					<FormGroup>
            <Label for="exec_time">Время выполнения</Label>
            <Input
              required
              type="time"
              name="exec_time"
              step="1"
              value={activeItem.exec_time}
              onChange={handleChange}
            />
          </FormGroup>

          <Button color="success">
            Сохранить
          </Button>
        </Form>
      </ModalBody>
    </Modal>
  );
}
export default OperationTypesModal;
