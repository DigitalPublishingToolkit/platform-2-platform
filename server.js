require('dotenv').config()
const express = require('express')
const app = express()
const port = 3000
const pg = require('pg')
const pg_format = require('pg-format')
const child_proc = require('child_process')

const config = {
  user: process.env.DB_USER,
  database: process.env.DB_HOST,
  password: process.env.DB_USER,
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

      // const q_labels = pg_format('SELECT column_name FROM information_schema.columns WHERE table_name =%L', 'scraper')
      // dbclient.query(q_labels, (err, result) => {
      //   if (err) throw err
      //   console.log(result)
      //   return result.rows
      // })

      const query = pg_format('SELECT title, url, author, tags, mod, publisher, body FROM scraper WHERE publisher=%L', publisher)
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

app.get('/api/article/random', (req, res, next) => {
  try {
    pool.connect((err, client, done) => {
      if (err) throw err
      dbclient = client

      const query = pg_format('SELECT title, url, author, tags, mod, publisher, body FROM scraper ORDER BY random() limit 1')
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

app.post('/api/send', (req, res, next) => {
  try {
    const article = req.body

    const publishers = {
      'amateur-cities': 'ac',
      'online-open': 'oo',
      'open-set-reader': 'osr'
    }

    // we take pipenv virtual env path, so all modules are found
    // how do you get this PATH from some sys.env?

    child_proc.exec('which python', (err, stdout, stderr) => {
      if (err) throw err
      console.log(stdout)
    })

    // const trigger = child_proc.spawn('/Users/af-etc/.local/share/virtualenvs/prototype-kEp0yEqi/bin/python', ['main.py', publishers[article.publisher], 'tv'])

    // trigger.stdout.on('data', (data) => {
    //   console.log('lala ---', data.toString())
    // })

    // function xx () {
    //   return new Promise((resolve, reject) => {
    //     spawn('python', ['main.py'], publishers[article.publisher], 'tv')
    //   })
    // }

    res.send('hi!!')
  } catch (err) {
    next(err)
  }
})

app.listen(port, () => {
  console.log(`listening on port${port}`)
})
