<!DOCTYPE html>
<html lang="zh-Hants">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Travel to Japan</title>
    <link
      rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.2.0/css/all.min.css"
      integrity="sha512-xh6O/CkQoPOWDdYTDqeRdPCVd1SpvCA9XXcUnZS2FmJNp1coAFzvtCN9BmamE+4aHK8yyUHUSCcJHgXloTyT2A=="
      crossorigin="anonymous"
      referrerpolicy="no-referrer"
    />
    <link rel="stylesheet" href="../public/styles/style.css" />
  </head>
  <body>
    <img class="fixed-image" src="./images/富士山2.jpg" alt="fixed-image" />

    <header>
      <section class="logo">
        <img src="./images/網站Logo.svg" alt="日本旅遊網Logo" />
        <h1>2025Travel to Japan</h1>
      </section>
      <nav>
        <ul>
          <li>
            <a href="#"><i class="fa-solid fa-plane"></i> Japanese Tourism</a>
          </li>
          <li>
            <a href="./views/checking.php"><i class="fa-solid fa-right-to-bracket"></i> Find Your Trip</a>
          </li>
          <li>
            <a href="./views/booking.php"><i class="fa-solid fa-book"></i> Make A Schedule</a>
          </li>
          <li>
            <a href="#"><i class="fa-regular fa-address-book"></i> Contact Us</a>
          </li>
        </ul>
      </nav>
    </header>

    <main>
      <section class="background-img">
        <div class="filter"></div>
        <h3>Leisure space, special holiday.<br />Plan a trip to Japan to relax and rejuvenate.</h3>
      </section>

      <section class="info-circles">
        <h3>Theme of Journey</h3>
        <div class="circles">
          <div class="circle">
            <img src="./images/北海道雪景.jpg" alt="北海道雪景" />
            <p>The snowy landscape of Hokkaido</p>
          </div>
          <div class="circle">
            <img src="./images/日本壽司.jpg" alt="日本壽司" />
            <p>Authentic sushi and cuisine</p>
          </div>
          <div class="circle">
            <img src="./images/富士山.jpg" alt="富士山" />
            <p>Mount Fuji scenery and hot springs</p>
          </div>
          <div class="circle">
            <img src="./images/清水寺.jpg" alt="清水寺" />
            <p>The beautiful Kiyomizu-dera in Kyoto</p>
          </div>
        </div>
      </section>

      <section class="empty-container">
        <h3>Start planning today and find the best option.</h3>
      </section>

      <section class="google-map">
        <h3>Geography of Japan</h3>
        <p>
          Japan is located in East Asia, surrounded by the Pacific Ocean to the east,
          the Sea of Japan, Korea Strait, and East China Sea to the west, and bordering Siberia, the Korean Peninsula, and China. 
          To the south, it is close to Taiwan and the Mariana Islands, and to the north,
          it borders the Sea of Okhotsk and Russia's Sakhalin and Kuril Islands. Japan has a mild climate year-round, with distinct seasons. 
          The south is warmer, while the north is colder, especially in winter when the Sea of Japan side experiences heavy snow,
          and the Pacific side remains dry and sunny.
        </p>
        <iframe
          src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d5300755.760441594!2d137.10323600911116!3d35.18148688884259!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x34674e0fd77f192f%3A0xf54275d47c665244!2sJapan!5e0!3m2!1sen!2sus!4v1664253921541!5m2!1sen!2sus"
          style="border: 0"
          allowfullscreen=""
          loading="lazy"
          referrerpolicy="no-referrer-when-downgrade"
        ></iframe>
      </section>
    </main>

    <footer>
      <section class="logo">
        <img src="./images/網站Logo.svg" alt="logo" />
        <h3>2025Travel to Japan</h3>
      </section>
      <section class="links">
        <a href="#"><img src="./Icons/facebook.svg" alt="facebook" /></a>
        <a href="#"><img src="./Icons/instagram.svg" alt="instagram" /></a>
        <a href="#"><img src="./Icons/twitter.svg" alt="twitter" /></a>
        <a href="#"><img src="./Icons/youtube.svg" alt="youtube" /></a>
      </section>
    </footer>

    <script>
      setInterval(() => {
        let topBackground = document.querySelector("section.background-img");
        if (
          topBackground.style.backgroundImage == 'url("./images/日本櫻花.jpg")'
        ) {
          topBackground.style.backgroundImage = 'url("./images/京都古城.jpg")';
        } else if (
          topBackground.style.backgroundImage == 'url("./images/京都古城.jpg")'
        ) {
          topBackground.style.backgroundImage = 'url("./images/大阪街頭.jpg")';
        } else {
          topBackground.style.backgroundImage = 'url("./images/日本櫻花.jpg")';
        }
      }, 3000);
    </script>
  </body>
</html>
