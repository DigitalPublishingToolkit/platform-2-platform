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
  password: process.env.DB_PW,
  max: 10,
  ideTimeoutMillis: 30000
}

const pool = new pg.Pool(config)
let dbclient

// -- endpoints
app.use(express.json())

app.get('/api/articles', (req, res, next) => {
  try {
    pool.connect((err, client, done) => {
      if (err) throw err
      dbclient = client

      const query = pg_format('SELECT title, url, author, tags, mod, publisher, body FROM scraper')
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

app.post('/api/ask', (req, res, next) => {
  try {
    // send an object like = {
    //   title: true / false;
    //   author: true / false;
    //   tags: true / false;
    //   body: true / false
    // }

    const article = req.body

    const publishers = {
      'amateur-cities': 'ac',
      'online-open': 'oo',
      'open-set-reader': 'osr'
    }

    const trigger = child_proc.spawn(process.env.PY_ENV, ['main.py', publishers[article.publisher], 'tv'])

    trigger.stdout.on('data', (data) => {
      console.log('lala ---', data.toString())
      res.send(data.toString())
    })

    // function xx () {
    //   return new Promise((resolve, reject) => {
    //     spawn('python', ['main.py'], publishers[article.publisher], 'tv')
    //   })
    // }
  } catch (err) {
    next(err)
  }
})

app.post('/api/send', (req, res, next) => {
  try {
    // send object like = {
    //   input_title: '',
    //   input_pub: '',
    //   match_title: '',
    //   match_pub: '',
    //   score: integer,
    //   timestamp: new Date().toISOString()
    // }

    const data = req.body
    console.log(data)

    pool.connect((err, client, done) => {
      const shouldAbort = err => {
        if (err) {
          console.error('Error in transaction', err.stack)
          client.query('ROLLBACK', err => {
            if (err) {
              console.error('Error rolling back client', err.stack)
            }
            // release client back to pool
            done()
          })
        }
        return !!err
      }

      client.query('BEGIN', err => {
        if (shouldAbort(err)) return
        const query = 'INSERT INTO feedbacks (input_url, match_url, score, timestamp) VALUES ($1, $2, $2, $4)'
        client.query(query, [], (err, result) => {
          if (shouldAbort(err)) return

          client.query('COMMIT', err => {
            if (err) {
              console.error('Error committing transaction', err.stack)
            }
            done()
          })
        })
      })
    })

    res.send('sent! ok')
  } catch (err) {
    next(err)
  }
})

app.listen(port, () => {
  console.log(`listening on port${port}`)
})
