import amino
import database
import hashlib
import uuid
import os

client = amino.Client()

activity_modules = {
    "registering": {},
    "online": []
}

# Command Functions
def command_depor(data: amino.objects.Event, args):
    global tippings
   
    wiki = subclient.get_wiki_info(client.get_from_code("qj79l5").objectId).wiki
    tips = subclient.get_tipped_users(wikiId=wiki.wikiId)
    tippings = dict(zip(tips.author.userId, tips.totalTippedCoins))

    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None

    last_amount = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().last_tip_max_count
    if query_for in tippings:
        if tippings[query_for] == last_amount:
            subclient.send_message(data.message.chatId,
            "Você já fez o depósito.")
        
        elif tippings[query_for] > last_amount:
            print("Getting new tips to database...")
            additional_value = int(tippings[query_for]) - last_amount
            print("Additional value is: " + str(additional_value))
            userdata = database.session.query(database.User).filter_by(amino_profile_id=query_for).first()
            print("Getting amino_coins value...")
            actual_value = userdata.amino_coins_count
            print("updating...")
            userdata.amino_coins_count = actual_value + additional_value
            userdata.last_tip_max_count = int(tippings[query_for])
            print("commiting...")
            database.session.commit()
            subclient.send_message(data.message.chatId,
            f"Você fez o depósito de {additional_value} amino coins.")

    else:
        subclient.send_message(data.message.chatId,
            "Você ainda não fez um depósito na carteira!")
    
def command_retirar(data: amino.objects.Event, args):
    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None

    value = int(args[0])
    print("Getting available...")
    available_get = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().amino_coins_count

    if value <= available_get and value <= int(client.get_wallet_info().totalCoins):
        print("Getting entrypoint...")
        entrypoint_code = database.session.query(database.User).filter_by(amino_profile_id=query_for).first().entrypoint_id
        if entrypoint_code == "":
            subclient.send_message(data.message.chatId,
            f"Você precisa definir um ponto de entrada. Use +set @entrypoint [link do post para aplaudir]")
        userdata = database.session.query(database.User).filter_by(amino_profile_id=query_for).first()
        print("Updating...")
        userdata.amino_coins_count = available_get - value
        print("Commiting...")
        database.session.commit()
        print("Sending values...")
        print("Generating UUID...", end=" ")
        transaction = str(uuid.uuid4())
        print(transaction)
        subclient.send_coins(value, entrypoint_code, transactionId=transaction)
        subclient.send_message(data.message.chatId,
            f"Você retirou o valor de {value} amino coins.")
    
    else:
        if value > available_get:
            subclient.send_message(data.message.chatId,
            "Você não possui essa quantia de moedas!")
        elif value > int(client.get_wallet_info().totalCoins):
            subclient.send_message(data.message.chatId,
            "O banco não possui essa quantia de moedas!")
        else:
            print("Internal Error")


def command_set(data: amino.objects.Event, args):
    for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                query_for = user.userid
                break
    else:
        subclient.send_message(data.message.chatId,
        "Você não está logado!")
        return None
    
    if args[0] == "@entrypoint":
        idcode = client.get_from_code(args[1]).objectId
        database.session.query(database.User).filter_by(amino_profile_id=query_for).first().entrypoint_id = idcode
        database.session.commit()
        subclient.send_message(data.message.chatId,
            f"Entrypoint das moedas atualizado com sucesso para <$@{data.message.author.nickname}$>!",
            mentionUserIds=[data.message.author.userId]
            )
    else:
        subclient.send_message(data.message.chatId,
            f"Valor não reconhecido.",
            )

def command_login(data: amino.objects.Event, args):
    global IS_SENSITIVE
    IS_SENSITIVE = True
    chatType = subclient.get_chat_thread(data.message.chatId).type

    if chatType == 0:
        for user in activity_modules["online"]:
            if user.userid == data.message.author.userId:
                subclient.send_message(data.message.chatId,
                "Você já está logado!")
                break
        else:
            sign = args[0]
            password = hashlib.md5(args[1].encode("UTF-8")).hexdigest()
            query = database.session.query(database.User).filter_by(signature=sign).first()
            if query.password == password and query.signature == sign:
                subclient.send_message(data.message.chatId,
                "Fazendo login...")
                if query.amino_profile_id == data.message.author.userId:
                    activity_modules["online"].append(database.ActiveUser(data.message.author.userId, query.signature))
                    subclient.send_message(data.message.chatId,
                    "Login realizado!")
                else:
                    subclient.send_message(data.message.chatId,
                    "Você não está no mesmo perfil no qual essa conta foi registrada.")
    else:
        subclient.send_message(data.message.chatId,
        f"Olá <$@{data.message.author.nickname}$>! Infelizmente, não posso executar esse comando em um chat público. :(\nPor favor, me mande mensagem no privado que poderei ajudar você! ;)",
        mentionUserIds=[data.message.author.userId])


def command_registrar(data: amino.objects.Event, args):
    global IS_SENSITIVE
    chatType = subclient.get_chat_thread(data.message.chatId).type

    if chatType == 0:
        if len(args) == 0: # HELP MESSAGE IF NOTHING
            subclient.send_message(data.message.chatId, 
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
                        subclient.send_message(
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
                        subclient.send_message(
                            data.message.chatId,
                            "Seu usuário já está reservado no módulo de atividade! Faça seu registro!"
                        )
                else:
                   subclient.send_message(
                            data.message.chatId,
                            "Você já possui um login!"
                        ) 
            
            elif args[0] == "@senha":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    pass_hash = hashlib.md5(args[1].encode("UTF-8")).hexdigest()
                    activity_modules["registering"][registering_userid]["password"] = pass_hash
                    subclient.send_message(
                        data.message.chatId,
                        f"Senha registrada para <$@{data.message.author.nickname}$>!",
                        mentionUserIds=[data.message.author.userId]
                    )
                else:
                    subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    ) 

            elif args[0] == "@assinatura":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    activity_modules["registering"][registering_userid]["signature"] = args[1]
                    subclient.send_message(
                        data.message.chatId,
                        f"Assinatura registrada para <$@{data.message.author.nickname}$>!",
                        mentionUserIds=[data.message.author.userId]
                    )
                else:
                    subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    )     

            elif args[0] == "@finalizar":
                if registering_userid in activity_modules["registering"]:
                    IS_SENSITIVE = True
                    subclient.send_message(
                            data.message.chatId,
                            f"Conferindo os dados..."
                        )

                    OKAY_LIST = [False, False] 
                    
                    if "password" in activity_modules["registering"][registering_userid]:
                        subclient.send_message(
                            data.message.chatId,
                            f"Senha OKAY"
                        )
                        OKAY_LIST[0] = True
                    else:
                        subclient.send_message(
                            data.message.chatId,
                            f"Senha FALHA"
                        )
                        OKAY_LIST[0] = False

                    if "signature" in activity_modules["registering"][registering_userid]:
                        subclient.send_message(
                            data.message.chatId,
                            f"Assinatura OKAY"
                        )
                        OKAY_LIST[1] = True
                    else:
                        subclient.send_message(
                            data.message.chatId,
                            f"Assinatura FALHA"
                        )
                        OKAY_LIST[1] = False
                    
                    if False in OKAY_LIST:
                        subclient.send_message(
                            data.message.chatId,
                            f"Há um campo vazio ou faltando, certifique que registrou os dois campos necessários."
                        )
                    else:
                        subclient.send_message(
                            data.message.chatId,
                            f"Dados preenchidos, verificando se assinatura é única..."
                        )
                        query = database.session.query(database.User).filter_by(
                            signature=activity_modules["registering"][registering_userid]["signature"]
                            ).first()

                        if query:
                            subclient.send_message(
                                data.message.chatId,
                                f"Sua assinatura não é única! Insira uma assinatura única."
                            )
                        else:
                            subclient.send_message(
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
                                subclient.send_message(
                                data.message.chatId,
                                f"Ocorreu um erro interno! Por favor, envie os dados novamente com +registrar @finalizar"
                            )
                        
                            finally:
                                del activity_modules["registering"][registering_userid]

                                subclient.send_message(
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
                    subclient.send_message(
                        data.message.chatId,
                        "Seu usuário não está reservado no módulo de atividade ou você já está registrado! Use +registrar @me!"
                    )

    
    else:
        subclient.send_message(data.message.chatId,
        f"Olá <$@{data.message.author.nickname}$>! Infelizmente, não posso executar esse comando em um chat público. :(\nPor favor, me mande mensagem no privado que poderei ajudar você! ;)",
        mentionUserIds=[data.message.author.userId])
        subclient.start_chat([data.message.author.userId])
        

def command_banktotal(data: amino.objects.Event, args):
    subclient.send_message(data.message.chatId, 
    f"Atualmente, tenho {int(client.get_wallet_info().totalCoins)} Amino Coins na minha carteira. :)")

def command_ping(data: amino.objects.Event, args):
    subclient.send_message(
        data.message.chatId, 
        f"pong! <$@{data.message.author.nickname}$>", 
        mentionUserIds=[data.message.author.userId])

def execute_command(command, data, args):
    if command in command_list and bot_nickname != data.message.author.nickname:
        try:
            command_list[command](data, args)
        except:
            subclient.send_message(
                data.message.chatId,
                "Ocorreu um erro!")
    else:
        subclient.send_message(
                data.message.chatId,
                "Comando inválido")


# Client Events
@client.event("on_text_message")
def on_text_message(data: amino.objects.Event):
    global bot_nickname, IS_ON, IS_SENSITIVE
    message = str(data.message.content)
    bot_nickname = subclient.get_account_info().nickname
    
    if message.startswith("+"):
        message = message.replace("+", "").split(" ")
        execute_command(message[0], data, message[1:] if len(message) >= 2 else [])

    print(f"{data.message.author.nickname}: {data.message.content}" if IS_ON and not IS_SENSITIVE else "")
    IS_SENSITIVE = False

# Setup Bot client and subclient
def setup_bot():
    global client, subclient, command_list
    command_list = {
        "ping": command_ping,
        "banktotal": command_banktotal,
        "registrar": command_registrar,
        "login": command_login,
        "set": command_set,
        "retirar": command_retirar,
        "depor": command_depor
    }

    client.login(os.environ["BOT_EMAIL"], os.environ["BOT_PASSWORD"])
    subclient = amino.SubClient(aminoId="Programaspy", profile=client.profile)

    # Show bot status
    print(60*"=")
    print("Mona | Bot is up! Starting getting messages...")
    print(60*"=", "\n")

    global IS_ON, IS_SENSITIVE, tippings
    IS_ON = True
    IS_SENSITIVE = False

    wiki = subclient.get_wiki_info(client.get_from_code("qj79l5").objectId).wiki
    tips = subclient.get_tipped_users(wikiId=wiki.wikiId)
    tippings = dict(zip(tips.author.userId, tips.totalTippedCoins))

if __name__ == "__main__":
    setup_bot()