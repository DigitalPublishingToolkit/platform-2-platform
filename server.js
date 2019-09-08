const express = require('express')
const app = express()
const port = 3000
const pg = require('pg')
const pg_format = require('pg-format')

const config = {
  user: 'andre',
  database: 'make_it_public',
  max: 10,
  ideTimeoutMillis: 30000
}

const pool = new pg.Pool(config)
let dbclient

// -- endpoints
app.use(express.json())

app.get('/api/articles/:id', (req, res, next) => {
  try {
    const publisher = req.params.id
    pool.connect((err, client, done) => {
      if (err) throw err 
      dbclient = client

      const q_labels = pg_format('SELECT column_name FROM information_schema.columns WHERE table_name =%L', 'scraper')
      // dbclient.query(q_labels, (err, result) => {
      //   if (err) throw err
      //   console.log(result)
      //   return result.rows
      // })

      const query = pg_format('SELECT title, url, author, tags, mod, body FROM scraper WHERE publisher=%L', publisher)
      dbclient.query(query, (err, result) => {
        if (err) throw err
        console.log(result.rows)
        const data = result.rows
        res.send(data)
      })
    })
  } catch (err) {
    next(err)
  }
})

app.listen(port, () => {
  console.log(`listening on port${port}`)
})
