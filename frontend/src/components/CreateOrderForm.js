import React, { useEffect, useState, useContext } from "react";
import DeleteIcon from '@mui/icons-material/Delete';
import {
  TextField, Typography, InputLabel, Select, MenuItem, OutlinedInput,
  Box, Stack, Grid,
  Table, TableContainer, TableHead, TableBody, TableRow, TableCell,
  Button, Paper, FormControl
} from "@mui/material";
import { useNavigate } from "react-router-dom";

import ToothMarks from "./ToothMarks";
import productTypesService from "../servicies/ProductTypesService";
import orderService from "../servicies/OrderService";
import AuthContext from '../context/AuthContext';


const CreateOrderForm = () => {
  let { authTokens } = useContext(AuthContext);
  let [listOfProducts, setListOfProducts] = useState([]);
  let [allProductTypes, setAllProductTypes] = useState([]);
  let [selectedProductType, setSelectedProductType] = useState("");
  let [orderCost, setOrderCost] = useState(0);

  // States for dental formula
  const [upperJaw, setUpperJaw] = useState([]);
  const [lowerJaw, setLowerJaw] = useState([]);
  const [markedTeeth, setMarkedTeeth] = useState(new Set());

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
        console.log(res.data);
        let products = res.data.map(product => {
          return {
            key: product.id,
            value: product.name,
            cost: product.cost
          }
        });

        setAllProductTypes(products);
        if (products.length > 0) {
          setSelectedProductType(products[0].value);
        }
      })
      .catch(err => console.log(err));
  }, [])

  const saveProduct = (e) => {
    e.preventDefault();

    const productType = allProductTypes.find((val, _) => val.value === selectedProductType);
    const sumCost = productType.cost * e.target.amount.value;
    setOrderCost(orderCost + sumCost);

    const product = {
      "product_type_id": productType.key,
      "product_type_name": productType.value,
      "product_type_cost": productType.cost,
      "sum_cost": sumCost,
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
      setOrderCost(orderCost - product.sum_cost);
    }
  }

  const renderProducts = () => {
    let i = 1;
    return listOfProducts.map((product) => (
      <TableRow>
        <TableCell>{i++}</TableCell>
        <TableCell>{product.product_type_name}</TableCell>
        <TableCell>{product.amount}</TableCell>
        <TableCell>{product.product_type_cost.toFixed(2)}</TableCell>
        <TableCell>{product.sum_cost.toFixed(2)}</TableCell>
        <TableCell><ToothMarks teethList={product.teeth} /></TableCell>
        <TableCell>
          <Button className="px-0" onClick={() => handleDelete(product)} >
            <DeleteIcon />
          </Button>
        </TableCell>
      </TableRow>
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
        width: 30,
        height: 30,
        backgroundColor: background,
        color: color,
        border: '1px solid black',
        borderRadius: "50%",
        textAlign: 'center'
      }}>
        <p> {number}</p>
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
    <Grid container sx={{
      spacing: 0,
      direction: "column",
      alignItems: "center",
      justifyContent: "center"
    }}>
      <Stack container sx={{
        display: "flex",
        width: "72%",
        minWidth: "500px",
        spacing: 3
      }}>
        <Box sx={{
          border: 1,
          borderRadius: 2,
          borderColor: '#4d4c4c',
          padding: 3,
          marginTop: 5,
        }}>
          <Typography variant="h4" component="h4" sx={{
            textAlign: "center",
            marginBottom: 2
          }}>
            Оформление заказа
          </Typography>
          <Box>
            <form onSubmit={saveProduct}>
              <FormControl sx={{ 
                paddingBlockEnd: 3, 
                display: 'flex', 
                flexDirection: 'row' 
              }}>
                <InputLabel>Тип изделия</InputLabel>
                <Select
                  required
                  name="product_type"
                  onChange={e => setSelectedProductType(e.target.value)}
                  value={selectedProductType}
                  input={<OutlinedInput label="Тип изделия" />}
                >
                  {allProductTypes.map(prod => (
                    <MenuItem value={prod.value}>{prod.value}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl sx={{ paddingBlockEnd: 3 }}>
                <TextField
                  label="Количество"
                  required
                  type="number"
                  name="amount"
                  min="1" max="32" step="1"
                  defaultValue={1}
                />
              </FormControl><br />

              <FormControl sx={{ paddingBlockEnd: 3 }}>
                <Typography>Зубная формула</Typography>
                <TableContainer component={Paper} sx={{ padding: 1 }}>
                  <Table>
                    <TableBody>
                      <TableRow>
                        {upperJaw.map(tooth => {
                          return <td>{getToothMark(tooth)}</td>
                        })}
                      </TableRow>
                      <TableRow>
                        {lowerJaw.map(tooth => {
                          return <td>{getToothMark(tooth)}</td>
                        })}
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </FormControl><br />

              <Button variant="contained" color="success" type="submit">
                Добавить изделие
              </Button>
            </form>
          </Box>

          <Box sx={{
            border: 1,
            borderRadius: 2,
            borderColor: '#4d4c4c',
            padding: 3,
            marginTop: 5,
          }}>
            {
              listOfProducts.length > 0 ?
                <div sx={{ display: "inline-block" }}>
                  <Typography textAlign={"center"} variant="h6" component="h6">
                    Выбранные изделия
                  </Typography>
                  <Typography sx={{ marginY: 2 }}>
                    Сумма: {orderCost.toFixed(2)} руб.
                  </Typography>
                  <Button variant="contained" type="button" onClick={sendOrder} sx={{
                    color: "primary",
                    marginBottom: 2
                  }}>
                    Заказать
                  </Button>
                  <TableContainer component={Paper}>
                    <TableHead>
                      <TableRow>
                        <TableCell>№</TableCell>
                        <TableCell>Тип изделия</TableCell>
                        <TableCell>Кол-во</TableCell>
                        <TableCell>Цена за 1 шт.</TableCell>
                        <TableCell>Сумма</TableCell>
                        <TableCell>Отметки</TableCell>
                        <TableCell></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {renderProducts()}
                    </TableBody>
                  </TableContainer>
                </div>
                :
                <div textAlign={"center"}>
                  Еще ни одного изделия для заказа не добавлено
                </div>
            }
          </Box>
        </Box>
      </Stack>
    </Grid>
  );
}
export default CreateOrderForm;
