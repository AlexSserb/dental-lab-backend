import React, { useEffect, useState, useContext } from "react";
import DeleteIcon from '@mui/icons-material/Delete';
import Select from "react-select";
import { useNavigate } from "react-router-dom";
import {
  Table,
  Button,
  Form,
  FormGroup,
  Input,
  Label
} from "reactstrap";

import ToothMarks from "./ToothMarks";
import productTypesService from "./../servicies/ProductTypesService";
import orderService from "../servicies/OrderService";
import AuthContext from '../context/AuthContext';


const CreateOrderLayout = () => {
  let { authTokens } = useContext(AuthContext);
  let [ listOfProducts, setListOfProducts ] = useState([]);
  let [ allProductTypes, setAllProductTypes ] = useState([]);
  let [ selectedProductType, setSelectedProductType ] = useState({value: '', label: ''});

  // States for dental formula
  const [ upperJaw, setUpperJaw ] = useState([]);
	const [ lowerJaw, setLowerJaw ] = useState([]);
  const [ markedTeeth, setMarkedTeeth ] = useState(new Set());

  const navigate = useNavigate();

  useEffect(() => {
    if (!authTokens || !authTokens.access) {
      navigate('/login');
      return;
    }
    
    fillUpperJaw();
		fillLowerJaw();

    productTypesService.getAll(authTokens?.access)
      .then(res => {
        let products = res.data.map(product => { return { value: product.id, label: product.name }});
        
        setAllProductTypes(products);
        if (products.length > 0) {
          setSelectedProductType(products[0]);
        }
      })
      .catch(err => console.log(err));
  }, [])

  const saveProduct = (e) => {
    e.preventDefault();

    const product = {
      "product_type_id": selectedProductType.value,
      "product_type_name": selectedProductType.label,
      "amount": e.target.amount.value,
      "teeth": [...markedTeeth]
    };

    listOfProducts.push(product);

    const set = new Set();
    setMarkedTeeth(set);
  }

  const handleDelete = (product) => {
    let list = [...listOfProducts];
    const index = list.indexOf(product);

    if (index > -1) {
      list.splice(index, 1);
      setListOfProducts(list);
    }
  }

  const renderProducts = () => {
    let i = 1;
    return listOfProducts.map((product) => (
      <tr> 
        <td>{i++}</td>
        <td>{product.product_type_name}</td>
				<td>{product.amount}</td>
        <td><ToothMarks teethList={product.teeth}/></td>
        <td>
          <Button className="px-0" onClick={() => handleDelete(product)} >
            <DeleteIcon/>
          </Button>
        </td>
      </tr>
    ));
  }

  // Functions to fill in the dental formula in the form
  const fillUpperJaw = () => {
		let arrUpperJaw = [];
		for (let num = 18; num >= 11; num--) arrUpperJaw.push(num);
		for (let num = 21; num <= 28; num++) arrUpperJaw.push(num)
		setUpperJaw(arrUpperJaw);
	}
	const fillLowerJaw = () => {
		let arrLowerJaw = [];
		for (let num = 48; num >= 41; num--) arrLowerJaw.push(num);
		for (let num = 31; num <= 38; num++) arrLowerJaw.push(num);
		setLowerJaw(arrLowerJaw);
	}

  const getToothMark = (number) => {
		let background = markedTeeth.has(number) ? "black" : "white";
		let color = markedTeeth.has(number) ? "white" : "black";

		const onClickFunc = () => {
			const teeth = new Set(markedTeeth.values());

			if (!teeth.has(number)) {
				teeth.add(number);
			}
			else {
				teeth.delete(number);
			}

			setMarkedTeeth(teeth);
		}

		return (
			<button type="button" onClick={onClickFunc} style={{
				display: "flex",
				width: "31px",
				height: "31px",
				backgroundColor: background,
				color: color,
				border: '1px solid black',
				borderRadius: "50%",
				textAlign: 'center'
			}}>
				<p style={{paddingLeft : '1px'}}>{number}</p>
			</button>
		)
	}

  const sendOrder = () => {
    orderService.post(authTokens?.access, listOfProducts)
    .then(_ => {
      navigate("/");
      alert("Заказ успешно оформлен!");
    })
    .catch(err => console.log(err));
  }

  return (
		<div className="d-flex justify-content-center mx-5 px-5 mt-5">
      <div>
        <h3 className="text-center m-1">Оформление заказа</h3>
        <div className="card card-container mt-3">
          <Form onSubmit={saveProduct} className="m-4">
            <FormGroup>
              <Label for="product_type">Тип изделия</Label>
              <Select
                required
                name="product_type"
                onChange={setSelectedProductType}
                value={selectedProductType}
                options={allProductTypes} 
                placeholder="Выберите тип изделия"
              />
            </FormGroup>

            <FormGroup>
              <Label for="amount">Количество</Label>
              <Input
                required
                type="number"
                name="amount"
                min="1" max="32" step="1"
                defaultValue={1}
              />
            </FormGroup>

            <FormGroup>
              <Label for="teeth">Зубная формула</Label>
              <Table> 
                <tbody> 
                  <tr>
                    { upperJaw.map(tooth => {
                      return <td>{getToothMark(tooth)}</td>
                    })}
                  </tr>
                  <tr>
                    { lowerJaw.map(tooth => {
                      return <td>{getToothMark(tooth)}</td>
                    })}
                  </tr>
                </tbody> 
              </Table> 
            </FormGroup>

            <Button color="success">
              Добавить изделие
            </Button>
          </Form>
        </div>
        
        <div className="card card-container mt-3">
        {
          listOfProducts.length > 0 ? 
          <div className="mx-4" style={{display: "inline-block"}}>
            <h5 className="mx-2 mt-2 mb-0" for="products">Выбранные изделия</h5><br/>
            <Button className="mx-2 mb-2" type="button" color="primary" onClick={sendOrder}>
              Заказать
            </Button>
            <Table bordered> 
              <thead> 
                <tr> 
                  <th>№</th>
                  <th>Тип изделия</th> 
                  <th>Кол-во</th>
                  <th>Отметки</th>
                  <th></th>
                </tr> 
              </thead> 
              <tbody> 
                { renderProducts() }
              </tbody> 
            </Table> 
          </div>
          : 
          <Label className="text-center m-3" for="products">
            Еще ни одного изделия для заказа не добавлено
          </Label>
        }
        </div>
      </div>
    </div>
  );
}
export default CreateOrderLayout;
