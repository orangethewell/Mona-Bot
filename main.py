import time
import amino
import asyncio

from amino.lib.util.exceptions import NotOwnerOfChatBubble
import database
import hashlib
import uuid
import os

IS_ON = False
IS_SENSITIVE = False

client = amino.Client()

activity_modules = {
    "registering": {},
    "online": []
}

superusers = database.session.query(database.Admin).filter_by(privileges_level = 1).all()
superuser_request = []
pending = []

wikicode = "z9e7as"

# Other Functions
async def is_chat_private(subclient, chatId):
    chatType = (await subclient.get_chat_thread(chatId)).type
    if chatType == 0:
        return True
    else:
        return False

async def update_banktips_data(subclient):
    global tippings
    objectid = (await client.get_from_code(wikicode)).objectId
    wiki = (await subclient.get_wiki_info(objectid)).wiki
    tips = (await subclient.get_tipped_users(wikiId=wiki.wikiId))
    tippings = dict(zip(tips.author.userId, tips.totalTippedCoins))

# Command Functions
async def command_temporally_not_available(data: amino.objects.Event, subclient, args):
    await subclient.send_message(data.message.chatId,
        "Esse comando está temporariamente indisponível.")

async def command_getadmin(data: amino.objects.Event, subclient, args):
    global superusers, superuser_request, pending
    if len(args) == 0:
        if data.message.author.userId == (superuser.amino_profile_id for superuser in superusers):
            await subclient.send_message(
                data.message.chatId, 
                "Você já é um administrador"
            )
        elif data.message.author.userId in pending:
            await subclient.send_message(
                data.message.chatId, 
                "Você já pediu um código de autenticação"
            )
        else:
            await subclient.send_message(
                data.message.chatId,
                ("Envie o código de autenticação que foi enviado no terminal por "
                "meio do comando +getadmin @auth [código]")
            )
            superuser_request.append(str(uuid.uuid4()))
            pending.append(data.message.author.userId)
            print(f"Authentication code: {superuser_request}")
    
    elif args[0] == "@auth":
        if args[1] in superuser_request:
            admin = database.Admin(
                amino_profile_id=data.message.author.userId,
                privileges_level=1
            )
            database.session.add(admin)
            database.commit()
            superusers = database.session.query(database.Admin).filter_by(privileges_level = 1).all()
            if data.message.author.userId == (superuser.amino_profile_id for superuser in superusers):
                await subclient.send_message(
                    data.message.chatId, 
                    f"<$@{data.message.author.nickname}$> agora é um administrador!",
                    mentionUserIds=[data.message.author.userId]
                )
            superuser_request.remove(args[1])


async def command_depositar(data: amino.objects.Event, subclient, args):
    global tippings
    
    await update_banktips_data(subclient)

    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        await subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None

    last_amount = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().last_tip_max_count
    if query_for in tippings:
        if tippings[query_for] == last_amount:
            await subclient.send_message(data.message.chatId,
            "Você já fez o depósito.")
        
        elif tippings[query_for] > last_amount:
            additional_value = int(tippings[query_for]) - last_amount
            userdata = database.session.query(database.User).filter_by(amino_profile_id=query_for).first()
            actual_value = userdata.amino_coins_count
            userdata.amino_coins_count = actual_value + additional_value
            userdata.last_tip_max_count = int(tippings[query_for])
            database.session.commit()
            await subclient.send_message(data.message.chatId,
            f"Você fez o depósito de {additional_value} amino coins.")

    else:
        await subclient.send_message(data.message.chatId,
            "Você ainda não fez um depósito na carteira!")
    
async def command_retirar(data: amino.objects.Event, subclient, args):
    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        await subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None

    value = int(args[0])
    available_get = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().amino_coins_count

    if value <= available_get and value <= int(client.get_wallet_info().totalCoins):
        entrypoint_code = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().entrypoint_id
        if entrypoint_code == "":
            await subclient.send_message(data.message.chatId,
            f"Você precisa definir um ponto de entrada. Use +set @entrypoint [link do post para aplaudir]")
        userdata = database.session.query(database.User).filter_by(amino_profile_id=query_for).first()
        userdata.amino_coins_count = available_get - value
        database.session.commit()
        print("Generating UUID...", end=" ")
        transaction = str(uuid.uuid4())
        print(transaction)
        await subclient.send_coins(value, entrypoint_code, transactionId=transaction)
        await subclient.send_message(data.message.chatId,
            f"Você retirou o valor de {value} amino coins.")
    
    else:
        if value > available_get:
            await subclient.send_message(data.message.chatId,
            "Você não possui essa quantia de moedas!")
        elif value > int(client.get_wallet_info().totalCoins):
            await subclient.send_message(data.message.chatId,
            "O banco não possui essa quantia de moedas!")
        else:
            print("Internal Error")


async def command_set(data: amino.objects.Event, subclient, args):
    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        await subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None
    
    if args[0] == "@entrypoint":
        idcode = client.get_from_code(args[1]).objectId
        database.session.query(database.User).filter_by(amino_profile_id=query_for).first().entrypoint_id = idcode
        database.session.commit()
        await subclient.send_message(data.message.chatId,
            f"Entrypoint das moedas atualizado com sucesso para <$@{data.message.author.nickname}$>!",
            mentionUserIds=[data.message.author.userId]
            )
    else:
        await subclient.send_message(data.message.chatId,
            f"Valor não reconhecido.",
            )

async def command_login(data: amino.objects.Event, subclient, args):
    global IS_SENSITIVE
    IS_SENSITIVE = True

    if (await is_chat_private(subclient, data.message.chatId)):
        for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                await subclient.send_message(data.message.chatId,
                "Você já está logado!")
                break
        else:
            sign = args[0]
            password = hashlib.md5(args[1].encode("UTF-8")).hexdigest()
            query = database.session.query(database.User).filter_by(signature=sign).first()
            if query.password == password and query.signature == sign:
                await subclient.send_message(data.message.chatId,
                "Fazendo login...")
                if query.amino_profile_id == data.message.author.userId:
                    activity_modules["online"].append(database.ActiveUser(data.message.author.userId, query.signature))
                    await subclient.send_message(data.message.chatId,
                    "Login realizado!")
                else:
                    await subclient.send_message(data.message.chatId,
                    "Você não está no mesmo perfil no qual essa conta foi registrada.")
    else:
        await subclient.send_message(data.message.chatId,
        f"Olá <$@{data.message.author.nickname}$>! Infelizmente, não posso executar esse comando em um chat público. :(\nPor favor, me mande mensagem no privado que poderei ajudar você! ;)",
        mentionUserIds=[data.message.author.userId])
        return None


async def command_registrar(data: amino.objects.Event, subclient, args):
    global IS_SENSITIVE

    if (await is_chat_private(subclient, data.message.chatId)):
        if len(args) == 0: # HELP MESSAGE IF NOTHING
            await subclient.send_message(data.message.chatId, 
            (f"[C]Olá, <$@{data.message.author.nickname}$>!\n\n"
        
            "\tFico feliz que queira criar uma conta no meu banco! " 
            "Antes de tudo, preciso saber se quer mesmo se registrar "
            "ou se usou essa mensagem por engano, para isso, use esse "
            "mesmo comando para definir que vai se registrar como você "
            "mesmo, basta digitar +registrar @me que irei reservar seu "
            "usuário atual para prosseguir com a autenticação.\n\n"
            
            "Além disso, preciso de te passar algumas informações! "
            "O meu banco ainda não tem muitos recursos, o que pode "
            "ser para alguns algo ruim agora, mas prometo melhorar "
            "no futuro! Logo terei funções incríveis e poderá desfrutar "
            "Da segurança e de outras coisas do meu banco no amino!\n\n"

            "[IC] Nota de 15/07/2021\n\n"
            
            "Enfim, fico feliz por ter me escolhido! ^^"),
            mentionUserIds=[data.message.author.userId]
        )
        
        elif len(args) > 0: # REGISTERING
            registering_userid = data.message.author.userId
            if "@me" in args:
                query = database.session.query(database.User).filter_by(amino_profile_id=registering_userid).first()
                if not query:
                    if registering_userid not in activity_modules["registering"]:
                        activity_modules["registering"][registering_userid] = {}
                        await subclient.send_message(
                            data.message.chatId,
                            ("Seu usuário foi reservado no módulo de atividade!\n\n"
                            "Agora, para prosseguir, use +registrar @senha [sua senha] e "
                            "+registrar @assinatura [sua assinatura]. no fim, use +registrar " 
                            "@finalizar para que possamos mandar os dados para o banco de dados.\n\n"
                            "A assinatura será como seu usuário, você precisa dele para retirar e "
                            "depositar suas moedas na sua conta. Não coloque espaços pois apenas a "
                            "parte não espaçada será salva.")
                        )
                    else:
                        await subclient.send_message(
                            data.message.chatId,
                            "Seu usuário já está reservado no módulo de atividade! Faça seu registro!"
                        )
                else:
                    await subclient.send_message(
                            data.message.chatId,
                            "Você já possui um login!"
                        ) 
            
            elif args[0] == "@senha":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    pass_hash = hashlib.md5(args[1].encode("UTF-8")).hexdigest()
                    activity_modules["registering"][registering_userid]["password"] = pass_hash
                    await subclient.send_message(
                        data.message.chatId,
                        f"Senha registrada para <$@{data.message.author.nickname}$>!",
                        mentionUserIds=[data.message.author.userId]
                    )
                else:
                    await subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    ) 

            elif args[0] == "@assinatura":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    activity_modules["registering"][registering_userid]["signature"] = args[1]
                    await subclient.send_message(
                        data.message.chatId,
                        f"Assinatura registrada para <$@{data.message.author.nickname}$>!",
                        mentionUserIds=[data.message.author.userId]
                    )
                else:
                    await subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    )     

            elif args[0] == "@finalizar":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    await subclient.send_message(
                            data.message.chatId,
                            f"Conferindo os dados..."
                        )

                    OKAY_LIST = [False, False] 
                    
                    if "password" in activity_modules["registering"][registering_userid]:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Senha OKAY"
                        )
                        OKAY_LIST[0] = True
                    else:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Senha FALHA"
                        )
                        OKAY_LIST[0] = False

                    if "signature" in activity_modules["registering"][registering_userid]:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Assinatura OKAY"
                        )
                        OKAY_LIST[1] = True
                    else:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Assinatura FALHA"
                        )
                        OKAY_LIST[1] = False
                    
                    if False in OKAY_LIST:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Há um campo vazio ou faltando, certifique que registrou os dois campos necessários."
                        )
                    else:
                        await subclient.send_message(
                            data.message.chatId,
                            f"Dados preenchidos, verificando se assinatura é única..."
                        )
                        query = database.session.query(database.User).filter_by(
                            signature=activity_modules["registering"][registering_userid]["signature"]
                            ).first()

                        if query:
                            await subclient.send_message(
                                data.message.chatId,
                                f"Sua assinatura não é única! Insira uma assinatura única."
                            )
                        else:
                            await subclient.send_message(
                            data.message.chatId,
                            f"Enviando pro banco de dados..."
                            )
                            try:
                                print("Updating database...")
                                user = database.User(
                                    amino_profile_id=registering_userid,
                                    entrypoint_id="",
                                    amino_coins_count=0,
                                    last_tip_max_count=0,
                                    signature=activity_modules["registering"][registering_userid]["signature"],
                                    password=activity_modules["registering"][registering_userid]["password"]
                                    )
                            
                                database.session.add(user)
                                database.session.commit()
                                print("Database updated!")
                            
                            except:
                                print("An error ocurred pulling data for database!")
                                await subclient.send_message(
                                data.message.chatId,
                                f"Ocorreu um erro interno! Por favor, envie os dados novamente com +registrar @finalizar"
                            )
                        
                            finally:
                                del activity_modules["registering"][registering_userid]

                                await subclient.send_message(
                                    data.message.chatId,
                                    (f"Sua conta foi criada com sucesso, <$@{data.message.author.nickname}$>!\n\n"
                                    "A partir de agora, você está registrado no banco da Mona! E aqui vai algumas " 
                                    "coisinhas: Você ainda precisa dizer onde devo entregar seus amino coins! Basta "
                                    "me mandar o link do post onde posso fazer seus donativos com o comando "
                                    "+set @entrypoint [link do seu blog]. E, para fazer isso, você precisa logar "
                                    "na sua conta! use +login [assinatura] [senha] e irei fazer seu login!\n\n"
                                    "Além disso, como é a sua primeira vez, para depositar seu dinheiro, você "
                                    "entrará no meu perfil e fará seu aplauso com a quantia que quer depositar, "
                                    "depois irá rodar o comando +depor e eu carregarei os seu dinheiro no banco!\n\n"
                                    "E caso tenha algo a retirar, basta usar o comando +retirar para pegar seu "
                                    "dinheiro! \n\n"
                                    "[C]Por enquanto é só! Se divirta! :)"),
                                    mentionUserIds=[data.message.author.userId]
                                )
                else:
                    await subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    )

    
    else:
        await subclient.send_message(data.message.chatId,
        f"Olá <$@{data.message.author.nickname}$>! Infelizmente, não posso executar esse comando em um chat público. :(\nPor favor, me mande mensagem no privado que poderei ajudar você! ;)",
        mentionUserIds=[data.message.author.userId])
        await subclient.start_chat(data.message.author.userId, 
        message=(
            f"[C]Olá, {data.message.author.nickname}!\n\n"
        
            "\tFico feliz que queira criar uma conta no meu banco! " 
            "Antes de tudo, preciso saber se quer mesmo se registrar "
            "ou se usou essa mensagem por engano, para isso, use esse "
            "mesmo comando para definir que vai se registrar como você "
            "mesmo, basta digitar +registrar @me que irei reservar seu "
            "usuário atual para prosseguir com a autenticação.\n\n"
            
            "Além disso, preciso de te passar algumas informações! "
            "O meu banco ainda não tem muitos recursos, o que pode "
            "ser para alguns algo ruim agora, mas prometo melhorar "
            "no futuro! Logo terei funções incríveis e poderá desfrutar "
            "Da segurança e de outras coisas do meu banco no amino!\n\n"

            "[IC] Nota de 15/07/2021\n\n"
            
            "Enfim, fico feliz por ter me escolhido! ^^"))
        

async def command_banktotal(data: amino.objects.Event, subclient, args):
    await subclient.send_message(data.message.chatId, 
    f"Atualmente, tenho {int(client.get_wallet_info().totalCoins)} Amino Coins na minha carteira. :)")

async def command_ping(data: amino.objects.Event, subclient, args):
    await subclient.send_message(
        data.message.chatId, 
        f"pong 2.0! <$@{data.message.author.nickname}$>", 
        mentionUserIds=[data.message.author.userId])

async def execute_command(command, data, args):
    subclient = await amino.SubClient(aminoId="Programaspy", profile=client.profile)
    if command in command_list and bot_nickname != data.message.author.nickname:
        try:
            await command_list[command](data, subclient, args)
        except Exception as exception:
            await subclient.send_message(
                data.message.chatId,
                "Ocorreu um erro!")
            print(exception)
    else:
        await subclient.send_message(
                data.message.chatId,
                "Comando inválido")
    
    subclient.close()


# Client Events
@client.event("on_text_message")
async def on_text_message(data: amino.objects.Event):
    global bot_nickname, IS_ON, IS_SENSITIVE
    message = str(data.message.content)
    bot_nickname = "mona"
    
    if message.startswith("+"):
        message = message.replace("+", "").split(" ")
        await execute_command(message[0], data, message[1:] if len(message) >= 2 else [])

    print(f"{data.message.author.nickname}: {data.message.content}" if IS_ON and not IS_SENSITIVE else "")
    IS_SENSITIVE = False

# Setup Bot client and subclient
async def setup_bot():
    global client, command_list
    command_list = {
        "ping": command_ping,
        "banktotal": command_banktotal,
        "registrar": command_registrar, 
        "login": command_login, 
        "set": command_set, 
        "retirar": command_retirar, 
        "depositar": command_depositar, 
        "getadmin": command_getadmin, 
    }

    await client.login(os.environ["BOT_EMAIL"], os.environ["BOT_PASSWORD"])
    subclient = await amino.SubClient(aminoId="Programaspy", profile=client.profile)

    # Show bot status
    print(60*"=")
    print("Mona | Bot is up! Starting getting messages...")
    print(60*"=", "\n")

    global IS_ON, IS_SENSITIVE, tippings

    # Transfering wallet refered data
    await update_banktips_data(subclient)

    IS_ON = True
    IS_SENSITIVE = False
    while True:
        await asyncio.sleep(300)
        await client.session.close()
        await client.startup()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_bot())