Для тех, кто пользуется приложением `https://play.google.com/store/apps/details?id=ru.abrr.gas` или сайтом `https://мойгаз.смородина.онлайн/` для оплаты за газ.



Установка

1. Копируем папку с интеграцией в custom_components. Перезагружаем HA.

2. `Устройста и Службы` - `Добавить интеграцию`. Выбираем `"Личный кабинет Газпром МЕЖРЕГИОНГАЗ"`.
<img width="466" height="497" alt="image" src="https://github.com/user-attachments/assets/6405e901-d3e6-4e85-b104-ef7e54e31898" />

3. Вводи логин/пароль.
<img width="488" height="331" alt="image" src="https://github.com/user-attachments/assets/30bc4a89-f1cc-49a3-b3f8-0437154d4195" />

4. Появляются следующие сущности 
<img width="548" height="568" alt="image" src="https://github.com/user-attachments/assets/4c734daa-aafd-4792-97fe-31d0c2be25c6" />

Передача показаний осуществляется либо вводом показаний в соответствующее окошко и нажатиме кнопки `Передать показания` либо службой `action: gazprom_lk.send_indication` (показания должны быть целым числом, без десятичных знаков)
<img width="986" height="461" alt="image" src="https://github.com/user-attachments/assets/110b50ca-cd23-4910-af4a-9c80dff7459a" />

Аналогичным образом происходит обновление данных - кнопкой или службой. 
