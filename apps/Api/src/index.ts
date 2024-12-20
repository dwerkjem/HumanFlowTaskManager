import express from 'express';

const app = express();
const port = 3000;

app.use(express.json());

app.post('/echo', (req, res) => {
    res.json(req.body);
});

app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

app.listen(port, () => {
    console.log(`API is running on port ${port}`);
});